const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'bettergut',
  user: process.env.DB_USER || 'bettergut_user',
  password: process.env.DB_PASSWORD || 'bettergut_password',
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

async function connectDatabase() {
  try {
    const client = await pool.connect();
    console.log('✅ Database connection established');
    
    // Create tables if they don't exist
    await createTables(client);
    client.release();
    
    return pool;
  } catch (error) {
    console.error('❌ Database connection failed:', error);
    throw error;
  }
}

async function createTables(client) {
  const queries = [
    // Users table
    `CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY,
      email VARCHAR(255) UNIQUE NOT NULL,
      password_hash VARCHAR(255) NOT NULL,
      first_name VARCHAR(100),
      last_name VARCHAR(100),
      date_of_birth DATE,
      gender VARCHAR(20),
      height_cm INTEGER,
      weight_kg DECIMAL(5,2),
      activity_level VARCHAR(50) DEFAULT 'moderate',
      goals TEXT[],
      dietary_restrictions TEXT[],
      email_verified BOOLEAN DEFAULT FALSE,
      email_verification_token VARCHAR(500),
      email_verification_expires TIMESTAMP,
      password_reset_token VARCHAR(500),
      password_reset_expires TIMESTAMP,
      timezone VARCHAR(50) DEFAULT 'America/New_York',
      locale VARCHAR(10) DEFAULT 'en-US',
      last_login TIMESTAMP,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )`,
    
    // Food items table
    `CREATE TABLE IF NOT EXISTS food_items (
      id SERIAL PRIMARY KEY,
      name VARCHAR(255) NOT NULL,
      brand VARCHAR(255),
      barcode VARCHAR(50),
      category VARCHAR(100),
      serving_size VARCHAR(100),
      serving_unit VARCHAR(50),
      calories_per_serving DECIMAL(8,2),
      protein_g DECIMAL(8,2),
      carbs_g DECIMAL(8,2),
      fat_g DECIMAL(8,2),
      fiber_g DECIMAL(8,2),
      sugar_g DECIMAL(8,2),
      sodium_mg DECIMAL(8,2),
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )`,
    
    // Food tracking entries
    `CREATE TABLE IF NOT EXISTS food_entries (
      id SERIAL PRIMARY KEY,
      user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
      food_item_id INTEGER REFERENCES food_items(id),
      meal_type VARCHAR(50) NOT NULL,
      quantity DECIMAL(8,2) NOT NULL,
      unit VARCHAR(50),
      consumed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      notes TEXT,
      image_url VARCHAR(500),
      analyzed_by_llm BOOLEAN DEFAULT FALSE,
      llm_confidence DECIMAL(3,2),
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )`,
    
    // Daily nutrition summary
    `CREATE TABLE IF NOT EXISTS daily_nutrition (
      id SERIAL PRIMARY KEY,
      user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
      date DATE NOT NULL,
      total_calories DECIMAL(8,2) DEFAULT 0,
      total_protein DECIMAL(8,2) DEFAULT 0,
      total_carbs DECIMAL(8,2) DEFAULT 0,
      total_fat DECIMAL(8,2) DEFAULT 0,
      total_fiber DECIMAL(8,2) DEFAULT 0,
      total_sugar DECIMAL(8,2) DEFAULT 0,
      total_sodium DECIMAL(8,2) DEFAULT 0,
      meals_logged INTEGER DEFAULT 0,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id, date)
    )`,
    
    // User goals and targets
    `CREATE TABLE IF NOT EXISTS nutrition_goals (
      id SERIAL PRIMARY KEY,
      user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
      daily_calories INTEGER,
      daily_protein INTEGER,
      daily_carbs INTEGER,
      daily_fat INTEGER,
      daily_fiber INTEGER,
      daily_sodium INTEGER,
      weight_goal_kg DECIMAL(5,2),
      target_date DATE,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )`
  ];

  for (const query of queries) {
    try {
      await client.query(query);
    } catch (error) {
      console.error('Error creating table:', error);
      throw error;
    }
  }
  
  console.log('✅ Database tables created/verified');
}

module.exports = {
  pool,
  connectDatabase,
  query: (text, params) => pool.query(text, params)
};
