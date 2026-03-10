import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import joblib
import os
from src.utils.helpers import setup_logger

logger = setup_logger(__name__)

class LSTMPredictor:
    def __init__(self, sequence_length=60):
        self.model = None
        self.scaler = MinMaxScaler()
        self.sequence_length = sequence_length
        
    def build_model(self, input_shape):
        """Build LSTM model architecture"""
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        self.model = model
        logger.info("LSTM model built")
        
    def prepare_data(self, prices):
        """Prepare sequences for LSTM"""
        data = prices.values.reshape(-1, 1)
        scaled_data = self.scaler.fit_transform(data)
        
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i, 0])
            y.append(scaled_data[i, 0])
        
        X = np.array(X)
        y = np.array(y)
        
        # Reshape for LSTM (samples, timesteps, features)
        X = X.reshape(X.shape[0], X.shape[1], 1)
        
        return X, y
    
    def train(self, prices, epochs=50, batch_size=32, validation_split=0.1):
        """Train LSTM model on historical prices"""
        X, y = self.prepare_data(prices)
        
        if self.model is None:
            self.build_model((X.shape[1], 1))
        
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=0
        )
        
        logger.info(f"LSTM training completed. Final loss: {history.history['loss'][-1]:.6f}")
        return history
    
    def predict_next(self, last_sequence):
        """Predict next price"""
        if self.model is None:
            logger.error("Model not trained")
            return None
        
        last_sequence_scaled = self.scaler.transform(last_sequence.reshape(-1, 1))
        last_sequence_scaled = last_sequence_scaled.reshape(1, self.sequence_length, 1)
        
        pred_scaled = self.model.predict(last_sequence_scaled, verbose=0)
        pred = self.scaler.inverse_transform(pred_scaled)
        
        return pred[0, 0]
    
    def save(self, model_path, scaler_path):
        """Save model and scaler"""
        if self.model:
            self.model.save(model_path)
            joblib.dump(self.scaler, scaler_path)
            logger.info(f"Model saved to {model_path}")
    
    def load(self, model_path, scaler_path):
        """Load model and scaler"""
        if os.path.exists(model_path):
            self.model = tf.keras.models.load_model(model_path)
            self.scaler = joblib.load(scaler_path)
            logger.info(f"Model loaded from {model_path}")
        else:
            logger.error(f"Model file not found: {model_path}")