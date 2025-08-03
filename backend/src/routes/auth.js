const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const Joi = require('joi');
const db = require('../config/database');
const emailService = require('../services/emailService');

const router = express.Router();

// Validation schemas
const registerSchema = Joi.object({
  email: Joi.string().email().required(),
  password: Joi.string().min(6).required(),
  firstName: Joi.string().min(1).max(100),
  lastName: Joi.string().min(1).max(100)
});

const loginSchema = Joi.object({
  email: Joi.string().email().required(),
  password: Joi.string().required()
});

// Register new user
router.post('/register', async (req, res, next) => {
  try {
    const { error, value } = registerSchema.validate(req.body);
    if (error) {
      return res.status(400).json({
        error: 'Validation failed',
        details: error.details.map(d => d.message)
      });
    }

    const { email, password, firstName, lastName } = value;

    // Check if user already exists
    const existingUser = await db.query(
      'SELECT id, email_verified FROM users WHERE email = $1',
      [email]
    );

    if (existingUser.rows.length > 0) {
      const user = existingUser.rows[0];
      if (user.email_verified) {
        return res.status(409).json({ error: 'Email already registered and verified' });
      } else {
        // User exists but not verified, allow re-registration
        await db.query('DELETE FROM users WHERE email = $1 AND email_verified = FALSE', [email]);
      }
    }

    // Hash password
    const saltRounds = 12;
    const passwordHash = await bcrypt.hash(password, saltRounds);

    // Generate email verification token
    const verificationToken = emailService.generateVerificationToken(null, email);

    // Create user (unverified)
    const result = await db.query(
      `INSERT INTO users (email, password_hash, first_name, last_name, email_verification_token, timezone, locale) 
       VALUES ($1, $2, $3, $4, $5, $6, $7) 
       RETURNING id, email, first_name, last_name, email_verified, created_at`,
      [email, passwordHash, firstName, lastName, verificationToken, 'America/New_York', 'en-US']
    );

    const user = result.rows[0];

    // Send verification email
    try {
      await emailService.sendVerificationEmail(
        email, 
        firstName || 'there', 
        verificationToken
      );
    } catch (emailError) {
      console.error('Failed to send verification email:', emailError);
      // Don't fail registration if email fails, but log it
    }

    res.status(201).json({
      message: 'Account created successfully! Please check your email to verify your account.',
      user: {
        id: user.id,
        email: user.email,
        firstName: user.first_name,
        lastName: user.last_name,
        emailVerified: user.email_verified,
        createdAt: user.created_at
      },
      nextStep: 'email_verification'
    });
  } catch (error) {
    next(error);
  }
});

// Login user
router.post('/login', async (req, res, next) => {
  try {
    const { error, value } = loginSchema.validate(req.body);
    if (error) {
      return res.status(400).json({
        error: 'Validation failed',
        details: error.details.map(d => d.message)
      });
    }

    const { email, password } = value;

    // Find user
    const result = await db.query(
      'SELECT id, email, password_hash, first_name, last_name, email_verified FROM users WHERE email = $1',
      [email]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    const user = result.rows[0];

    // Check if email is verified
    if (!user.email_verified) {
      return res.status(403).json({ 
        error: 'Email not verified',
        message: 'Please verify your email before logging in. Check your inbox for the verification link.',
        nextStep: 'email_verification'
      });
    }

    // Verify password
    const isValidPassword = await bcrypt.compare(password, user.password_hash);
    if (!isValidPassword) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    // Generate JWT token
    const token = jwt.sign(
      { userId: user.id, email: user.email },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
    );

    res.json({
      message: 'Login successful',
      user: {
        id: user.id,
        email: user.email,
        firstName: user.first_name,
        lastName: user.last_name,
        emailVerified: user.email_verified
      },
      token
    });
  } catch (error) {
    next(error);
  }
});

// Email verification endpoint
router.get('/verify-email/:token', async (req, res, next) => {
  try {
    const { token } = req.params;

    if (!token) {
      return res.status(400).json({ error: 'Verification token required' });
    }

    // Verify and decode the token
    const decoded = emailService.verifyEmailToken(token);
    if (!decoded || !decoded.email) {
      return res.status(400).json({ error: 'Invalid or expired verification token' });
    }

    // Find user and verify email
    const result = await db.query(
      `UPDATE users 
       SET email_verified = TRUE, email_verification_token = NULL, updated_at = CURRENT_TIMESTAMP 
       WHERE email = $1 AND email_verification_token = $2 
       RETURNING id, email, first_name, last_name, email_verified`,
      [decoded.email, token]
    );

    if (result.rows.length === 0) {
      return res.status(400).json({ 
        error: 'Invalid verification token',
        message: 'This verification link may have expired or already been used.'
      });
    }

    const user = result.rows[0];

    res.json({
      message: 'Email verified successfully! You can now log in to your account.',
      user: {
        id: user.id,
        email: user.email,
        firstName: user.first_name,
        lastName: user.last_name,
        emailVerified: user.email_verified
      }
    });
  } catch (error) {
    console.error('Email verification error:', error);
    if (error.name === 'JsonWebTokenError' || error.name === 'TokenExpiredError') {
      return res.status(400).json({ 
        error: 'Invalid or expired verification token',
        message: 'Please request a new verification email.'
      });
    }
    next(error);
  }
});

// Resend verification email
router.post('/resend-verification', async (req, res, next) => {
  try {
    const { email } = req.body;

    if (!email) {
      return res.status(400).json({ error: 'Email address required' });
    }

    // Find user
    const result = await db.query(
      'SELECT id, email, first_name, email_verified FROM users WHERE email = $1',
      [email]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'No account found with this email address' });
    }

    const user = result.rows[0];

    if (user.email_verified) {
      return res.status(400).json({ 
        error: 'Email already verified',
        message: 'This email address is already verified. You can log in to your account.'
      });
    }

    // Generate new verification token
    const verificationToken = emailService.generateVerificationToken(user.id, user.email);

    // Update user with new token
    await db.query(
      'UPDATE users SET email_verification_token = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2',
      [verificationToken, user.id]
    );

    // Send verification email
    try {
      await emailService.sendVerificationEmail(
        user.email, 
        user.first_name || 'there', 
        verificationToken
      );

      res.json({
        message: 'Verification email sent! Please check your inbox and follow the instructions.',
        email: user.email
      });
    } catch (emailError) {
      console.error('Failed to send verification email:', emailError);
      return res.status(500).json({ 
        error: 'Failed to send verification email',
        message: 'Please try again later or contact support if the problem persists.'
      });
    }
  } catch (error) {
    next(error);
  }
});

// Refresh token
router.post('/refresh', async (req, res, next) => {
  try {
    const { refreshToken } = req.body;
    
    if (!refreshToken) {
      return res.status(401).json({ error: 'Refresh token required' });
    }

    const decoded = jwt.verify(refreshToken, process.env.JWT_SECRET);
    
    // Generate new token
    const newToken = jwt.sign(
      { userId: decoded.userId, email: decoded.email },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
    );

    res.json({ token: newToken });
  } catch (error) {
    res.status(403).json({ error: 'Invalid refresh token' });
  }
});

module.exports = router;
