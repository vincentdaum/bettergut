const nodemailer = require('nodemailer');
const crypto = require('crypto');
const jwt = require('jsonwebtoken');

class EmailService {
  constructor() {
    this.transporter = nodemailer.createTransporter({
      host: process.env.SMTP_HOST || 'smtp.gmail.com',
      port: parseInt(process.env.SMTP_PORT) || 587,
      secure: process.env.SMTP_SECURE === 'true',
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS
      }
    });
    
    this.fromEmail = process.env.FROM_EMAIL || 'noreply@bettergut.com';
    this.fromName = process.env.FROM_NAME || 'BetterGut Health';
    this.serverUrl = process.env.SERVER_URL || 'http://localhost:3000';
  }

  generateVerificationToken(userId, email) {
    return jwt.sign(
      { userId, email, type: 'email_verification' },
      process.env.EMAIL_VERIFICATION_SECRET || process.env.JWT_SECRET,
      { expiresIn: process.env.VERIFICATION_TOKEN_EXPIRES || '24h' }
    );
  }

  generateVerificationLink(token) {
    return `${this.serverUrl}/api/auth/verify-email?token=${token}`;
  }

  async sendVerificationEmail(userEmail, userName, verificationToken) {
    const verificationLink = this.generateVerificationLink(verificationToken);
    
    const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Verify Your BetterGut Account</title>
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; }
        .container { max-width: 600px; margin: 0 auto; background: white; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center; }
        .logo { color: white; font-size: 28px; font-weight: bold; margin: 0; }
        .content { padding: 40px 20px; }
        .welcome { font-size: 24px; color: #1a202c; margin-bottom: 20px; }
        .message { font-size: 16px; line-height: 1.6; color: #4a5568; margin-bottom: 30px; }
        .button { display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; padding: 16px 32px; border-radius: 8px; font-weight: 600; margin: 20px 0; }
        .button:hover { opacity: 0.9; }
        .footer { background: #f7fafc; padding: 20px; text-align: center; color: #718096; font-size: 14px; }
        .security-note { background: #edf2f7; padding: 16px; border-radius: 8px; margin: 20px 0; font-size: 14px; color: #4a5568; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1 class="logo">🌱 BetterGut</h1>
        </div>
        
        <div class="content">
          <h2 class="welcome">Welcome to BetterGut, ${userName || 'there'}! 👋</h2>
          
          <p class="message">
            Thank you for joining BetterGut, the AI-powered app that helps Americans improve their gut health through personalized nutrition insights. We're excited to help you on your wellness journey!
          </p>
          
          <p class="message">
            To get started and secure your account, please verify your email address by clicking the button below:
          </p>
          
          <div style="text-align: center;">
            <a href="${verificationLink}" class="button">Verify My Email Address</a>
          </div>
          
          <div class="security-note">
            <strong>🔒 Security Note:</strong> This verification link will expire in 24 hours. If you didn't create a BetterGut account, you can safely ignore this email.
          </div>
          
          <p class="message">
            Once verified, you'll be able to:
            <br>• 📱 Track your meals with AI-powered food recognition
            <br>• 💩 Monitor your digestive health patterns
            <br>• 🧠 Get personalized gut health insights from our AI
            <br>• 🥗 Receive evidence-based nutrition recommendations
          </p>
          
          <p class="message">
            If the button doesn't work, copy and paste this link into your browser:
            <br><a href="${verificationLink}" style="color: #667eea; word-break: break-all;">${verificationLink}</a>
          </p>
        </div>
        
        <div class="footer">
          <p>BetterGut Health - Improving Gut Health for Americans</p>
          <p>This email was sent to ${userEmail}. If you have questions, contact us at support@bettergut.com</p>
        </div>
      </div>
    </body>
    </html>`;

    const textContent = `
Welcome to BetterGut!

Thank you for joining BetterGut, the AI-powered app for gut health. Please verify your email address to complete your registration.

Verification link: ${verificationLink}

This link will expire in 24 hours. If you didn't create an account, you can ignore this email.

Best regards,
The BetterGut Team
    `;

    try {
      await this.transporter.sendMail({
        from: `"${this.fromName}" <${this.fromEmail}>`,
        to: userEmail,
        subject: '🌱 Welcome to BetterGut - Verify Your Email',
        text: textContent,
        html: htmlContent
      });

      console.log(`Verification email sent to ${userEmail}`);
      return true;
    } catch (error) {
      console.error('Error sending verification email:', error);
      throw new Error('Failed to send verification email');
    }
  }

  async sendPasswordResetEmail(userEmail, userName, resetToken) {
    const resetLink = `${this.serverUrl}/api/auth/reset-password?token=${resetToken}`;
    
    const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Reset Your BetterGut Password</title>
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; }
        .container { max-width: 600px; margin: 0 auto; background: white; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center; }
        .logo { color: white; font-size: 28px; font-weight: bold; margin: 0; }
        .content { padding: 40px 20px; }
        .title { font-size: 24px; color: #1a202c; margin-bottom: 20px; }
        .message { font-size: 16px; line-height: 1.6; color: #4a5568; margin-bottom: 30px; }
        .button { display: inline-block; background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%); color: white; text-decoration: none; padding: 16px 32px; border-radius: 8px; font-weight: 600; margin: 20px 0; }
        .footer { background: #f7fafc; padding: 20px; text-align: center; color: #718096; font-size: 14px; }
        .security-note { background: #fed7d7; padding: 16px; border-radius: 8px; margin: 20px 0; font-size: 14px; color: #742a2a; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1 class="logo">🌱 BetterGut</h1>
        </div>
        
        <div class="content">
          <h2 class="title">Password Reset Request 🔑</h2>
          
          <p class="message">
            Hi ${userName || 'there'},
          </p>
          
          <p class="message">
            We received a request to reset your BetterGut password. Click the button below to create a new password:
          </p>
          
          <div style="text-align: center;">
            <a href="${resetLink}" class="button">Reset My Password</a>
          </div>
          
          <div class="security-note">
            <strong>🔒 Security Notice:</strong> This link will expire in 1 hour. If you didn't request a password reset, please ignore this email and your password will remain unchanged.
          </div>
          
          <p class="message">
            If the button doesn't work, copy and paste this link into your browser:
            <br><a href="${resetLink}" style="color: #667eea; word-break: break-all;">${resetLink}</a>
          </p>
        </div>
        
        <div class="footer">
          <p>BetterGut Health - Secure by design</p>
          <p>This email was sent to ${userEmail}</p>
        </div>
      </div>
    </body>
    </html>`;

    try {
      await this.transporter.sendMail({
        from: `"${this.fromName}" <${this.fromEmail}>`,
        to: userEmail,
        subject: '🔑 Reset Your BetterGut Password',
        html: htmlContent
      });

      console.log(`Password reset email sent to ${userEmail}`);
      return true;
    } catch (error) {
      console.error('Error sending password reset email:', error);
      throw new Error('Failed to send password reset email');
    }
  }

  verifyEmailToken(token) {
    try {
      const decoded = jwt.verify(
        token,
        process.env.EMAIL_VERIFICATION_SECRET || process.env.JWT_SECRET
      );
      
      if (decoded.type !== 'email_verification') {
        throw new Error('Invalid token type');
      }
      
      return decoded;
    } catch (error) {
      throw new Error('Invalid or expired verification token');
    }
  }

  async testConnection() {
    try {
      await this.transporter.verify();
      console.log('✅ Email service connection verified');
      return true;
    } catch (error) {
      console.error('❌ Email service connection failed:', error);
      return false;
    }
  }
}

module.exports = new EmailService();
