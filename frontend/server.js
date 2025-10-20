const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors'); //

// Load environment variables if you are using a .env file
// require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// --- MIDDLEWARE SETUP ---

// 2. USE CORS MIDDLEWARE
// This MUST be placed before your routes to ensure requests are not blocked.
// It allows your server to accept requests from different origins (like your frontend).
app.use(cors());

// Middleware to parse JSON bodies from incoming requests
app.use(express.json());

// --- DATABASE CONNECTION ---
// Replace 'YOUR_MONGODB_CONNECTION_STRING' with your actual Atlas connection string
const dbURI = process.env.MONGODB_URI || 'mongodb+srv://omkarputti14_db_user:SrNWlwf8PoWZPGGz@shecares.ofki4wx.mongodb.net/?retryWrites=true&w=majority&appName=SHECARES';

mongoose.connect(dbURI)
  .then(() => console.log('✅ Connected to MongoDB Atlas'))
  .catch((err) => console.error('❌ Could not connect to MongoDB Atlas', err));


// --- API ROUTES ---

// Example route for handling form submissions
// Make sure the path '/api/submit-form' matches what your frontend is calling
app.post('/api/submit-form', (req, res) => {
  // Add a console log here to CONFIRM the request is being received
  console.log('✅ Request received at /api/submit-form');
  console.log('Request body:', req.body);

  try {
    // Your logic to save data to the database would go here
    // const newSubmission = new YourModel(req.body);
    // await newSubmission.save();

    res.status(201).json({ message: 'Submission successful!' });
  } catch (error) {
    console.error('Error processing submission:', error);
    res.status(500).json({ message: 'Server error during submission.' });
  }
});


// Add other routes here...
// app.get('/api/data', (req, res) => { ... });


// --- START THE SERVER ---
app.listen(PORT, () => {
  console.log(`🚀 Backend running on http://localhost:${PORT}`);
});