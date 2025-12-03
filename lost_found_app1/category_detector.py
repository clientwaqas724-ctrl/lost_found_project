# category_detector.py
import numpy as np
from PIL import Image
import os
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import cv2

class AdvancedCategoryDetector:
    def __init__(self):
        # Expanded categories with more specific items
        self.categories = {
            'electronics': [
                'phone', 'laptop', 'tablet', 'charger', 'headphones', 'camera', 
                'earbuds', 'powerbank', 'smartwatch', 'calculator', 'usb', 'cable',
                'mouse', 'keyboard', 'speaker', 'adapter', 'battery'
            ],
            'books': [
                'book', 'notebook', 'textbook', 'diary', 'novel', 'magazine',
                'journal', 'dictionary', 'encyclopedia', 'manual', 'guidebook'
            ],
            'clothing': [
                'shirt', 'pants', 'jacket', 'hat', 'shoes', 'dress', 't-shirt', 
                'jeans', 'sweater', 'hoodie', 'shorts', 'skirt', 'coat', 'socks',
                'underwear', 'tie', 'scarf', 'gloves'
            ],
            'accessories': [
                'wallet', 'keys', 'bag', 'backpack', 'watch', 'jewelry', 
                'sunglasses', 'belt', 'purse', 'handbag', 'lanyard', 'keychain'
            ],
            'documents': [
                'id', 'passport', 'license', 'card', 'certificate', 'document',
                'folder', 'file', 'paper', 'notebook', 'diploma', 'receipt'
            ],
            'sports': [
                'ball', 'racket', 'equipment', 'bottle', 'gloves', 'shoes',
                'bat', 'helmet', 'jersey', 'trainers', 'goggles', 'fins',
                'skates', 'stick', 'dumbbell', 'yoga mat'
            ],
            'stationery': [
                'pen', 'pencil', 'notebook', 'marker', 'eraser', 'ruler',
                'sharpener', 'stapler', 'scissors', 'glue', 'tape', 'clip',
                'highlighter', 'calculator', 'folder', 'binder'
            ],
            'toys': [
                'toy', 'game', 'stuffed', 'doll', 'car', 'action figure',
                'puzzle', 'lego', 'board game', 'cards', 'dice', 'puzzle'
            ],
            'kitchen': [
                'bottle', 'container', 'utensil', 'lunchbox', 'thermos',
                'cup', 'plate', 'bowl', 'cutlery', 'knife', 'spoon', 'fork',
                'tupperware', 'flask', 'food container'
            ],
            'personal_care': [
                'brush', 'comb', 'cosmetic', 'perfume', 'deodorant',
                'toothbrush', 'toothpaste', 'soap', 'shampoo', 'conditioner',
                'lotion', 'cream', 'makeup', 'razor', 'mirror'
            ],
            'jewelry': [
                'ring', 'necklace', 'bracelet', 'earrings', 'pendant',
                'chain', 'brooch', 'anklet', 'cufflinks', 'tiara'
            ],
            'bags': [
                'backpack', 'purse', 'handbag', 'briefcase', 'suitcase',
                'duffel', 'tote', 'messenger', 'clutch', 'wallet'
            ],
            'school_supplies': [
                'backpack', 'notebook', 'binder', 'textbook', 'calculator',
                'pencil case', 'ruler', 'protractor', 'compass', 'locker'
            ],
            'musical_instruments': [
                'guitar', 'piano', 'violin', 'flute', 'drum', 'trumpet',
                'saxophone', 'harmonica', 'ukulele', 'keyboard'
            ],
            'tools': [
                'hammer', 'screwdriver', 'wrench', 'pliers', 'tape measure',
                'drill', 'saw', 'knife', 'multitool', 'flashlight'
            ],
            'other': ['miscellaneous', 'unknown', 'unidentified']
        }
        
        # Initialize ML model for image classification
        self.model = self._load_model()
        self.image_size = (224, 224)
        
    def _load_model(self):
        """Load pre-trained model for image classification"""
        try:
            # Using MobileNetV2 for efficient image classification
            base_model = MobileNetV2(weights='imagenet', include_top=False, 
                                   input_shape=(224, 224, 3))
            model = keras.Sequential([
                base_model,
                keras.layers.GlobalAveragePooling2D(),
                keras.layers.Dense(512, activation='relu'),
                keras.layers.Dropout(0.3),
                keras.layers.Dense(len(self.categories), activation='softmax')
            ])
            return model
        except Exception as e:
            print(f"Model loading failed: {e}")
            return None
    
    def detect_category(self, image_path, title="", description=""):
        """Detect category from image and text with enhanced ML capabilities"""
        text_data = f"{title} {description}".lower()
        
        # Text-based category detection
        text_category = self._detect_from_text(text_data)
        if text_category and text_category != 'other':
            return text_category
        
        # Image-based category detection
        if os.path.exists(image_path):
            image_category = self._detect_from_image(image_path)
            if image_category and image_category != 'other':
                return image_category
        
        return 'other'
    
    def _detect_from_text(self, text):
        """Enhanced text-based category detection"""
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        return None
    
    def _detect_from_image(self, image_path):
        """Enhanced image-based category detection using ML"""
        try:
            # Load and preprocess image
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Apply multiple detection methods
            ml_category = self._ml_image_classification(image)
            heuristic_category = self._heuristic_image_analysis(np.array(image))
            
            # Prioritize ML results, fall back to heuristics
            if ml_category and ml_category != 'other':
                return ml_category
            elif heuristic_category:
                return heuristic_category
                
        except Exception as e:
            print(f"Image analysis error: {e}")
        
        return 'other'
    
    def _ml_image_classification(self, image):
        """ML-based image classification"""
        if self.model is None:
            return None
            
        try:
            # Preprocess image for model
            image = image.resize(self.image_size)
            img_array = np.array(image)
            img_array = preprocess_input(img_array)
            img_array = np.expand_dims(img_array, axis=0)
            
            # Get prediction (simulated for now - you'd train this model)
            # In production, you'd use a trained model here
            predictions = self._simulate_ml_prediction(image)
            
            if predictions:
                return max(predictions, key=predictions.get)
                
        except Exception as e:
            print(f"ML classification error: {e}")
            
        return None
    
    def _simulate_ml_prediction(self, image):
        """Simulate ML predictions based on image analysis"""
        # This is a simplified simulation - replace with actual trained model
        img_array = np.array(image)
        
        # Basic color and shape analysis to simulate ML
        if self._looks_like_electronics(img_array):
            return {'electronics': 0.8, 'other': 0.2}
        elif self._looks_like_book(img_array):
            return {'books': 0.7, 'documents': 0.3}
        elif self._looks_like_clothing(img_array):
            return {'clothing': 0.75, 'accessories': 0.25}
        elif self._looks_like_jewelry(img_array):
            return {'jewelry': 0.8, 'accessories': 0.2}
        
        return {'other': 1.0}
    
    def _heuristic_image_analysis(self, img_array):
        """Enhanced heuristic image analysis"""
        if len(img_array.shape) != 3:
            return None
            
        h, w, _ = img_array.shape
        
        # Electronics detection
        if self._looks_like_electronics(img_array):
            return 'electronics'
        
        # Books detection
        elif self._looks_like_book(img_array):
            return 'books'
        
        # Clothing detection
        elif self._looks_like_clothing(img_array):
            return 'clothing'
        
        # Jewelry detection
        elif self._looks_like_jewelry(img_array):
            return 'jewelry'
        
        # Bags detection
        elif self._looks_like_bag(img_array):
            return 'bags'
        
        # Documents detection
        elif self._looks_like_document(img_array):
            return 'documents'
            
        return None
    
    def _looks_like_electronics(self, img_array):
        """Enhanced electronics detection"""
        h, w, _ = img_array.shape
        
        # Electronics often have rectangular shapes with specific aspect ratios
        aspect_ratio = w / h
        common_ratios = [16/9, 4/3, 16/10, 3/2]
        
        for ratio in common_ratios:
            if abs(aspect_ratio - ratio) < 0.3:
                return True
        
        # Check for metallic/sleek appearance
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (w * h)
        
        # Electronics often have high edge density
        return edge_density > 0.1
    
    def _looks_like_book(self, img_array):
        """Enhanced book detection"""
        h, w, _ = img_array.shape
        
        # Books are typically wider than tall
        aspect_ratio = w / h
        if 1.2 <= aspect_ratio <= 3.0:
            return True
            
        return False
    
    def _looks_like_clothing(self, img_array):
        """Enhanced clothing detection"""
        # Clothing often has varied colors and textures
        unique_colors = len(np.unique(img_array.reshape(-1, img_array.shape[2]), axis=0))
        
        # Calculate color variance
        color_variance = np.var(img_array, axis=(0, 1))
        avg_variance = np.mean(color_variance)
        
        return unique_colors > 10 and avg_variance > 100
    
    def _looks_like_jewelry(self, img_array):
        """Jewelry detection based on small, shiny objects"""
        h, w, _ = img_array.shape
        
        # Jewelry is often small and shiny
        if w < 200 or h < 200:  # Small object
            # Check for high brightness (shininess)
            hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
            brightness = np.mean(hsv[:,:,2])
            
            return brightness > 150  # Very bright/shiny
            
        return False
    
    def _looks_like_bag(self, img_array):
        """Bag detection based on shape and size"""
        h, w, _ = img_array.shape
        
        # Bags often have irregular but somewhat rectangular shapes
        aspect_ratio = w / h
        if 0.5 <= aspect_ratio <= 2.0:  # Reasonable bag proportions
            # Check for handles or straps (dark horizontal lines)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Look for horizontal lines (potential straps)
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            horizontal_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)
            
            return np.sum(horizontal_lines > 0) > 10
            
        return False
    
    def _looks_like_document(self, img_array):
        """Document detection - rectangular, paper-like"""
        h, w, _ = img_array.shape
        
        # Documents are typically rectangular with paper-like colors
        aspect_ratio = w / h
        if 0.7 <= aspect_ratio <= 1.4:  # Common document ratios
            # Check for paper-like colors (light, neutral)
            avg_color = np.mean(img_array, axis=(0, 1))
            color_variance = np.var(avg_color)
            
            # Paper is usually light and not too colorful
            return np.mean(avg_color) > 100 and color_variance < 1000
            
        return False

# Helper function to use in models
def detect_category_from_image(instance, image_field):
    """Enhanced helper function to detect category from image"""
    if image_field and hasattr(image_field, 'path'):
        detector = AdvancedCategoryDetector()
        detected_category = detector.detect_category(
            image_field.path, 
            getattr(instance, 'title', ''),
            getattr(instance, 'description', '')
        )
        
        from .models import Category
        category, created = Category.objects.get_or_create(
            name=detected_category.capitalize(),
            defaults={'description': f'Auto-detected {detected_category} category'}
        )
        return category
    return None

def auto_categorize_item(item_instance):
    """Automatically categorize an item based on image and text"""
    if hasattr(item_instance, 'item_image') and item_instance.item_image:
        category = detect_category_from_image(item_instance, item_instance.item_image)
        if category:
            item_instance.category = category
            return True
    return False