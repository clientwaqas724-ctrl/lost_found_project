# category_detector.py
import numpy as np
from PIL import Image
import os
import cv2

class PracticalCategoryDetector:
    def __init__(self):
        # Expanded categories with more specific items
        self.categories = {
            'electronics': [
                'phone', 'laptop', 'tablet', 'charger', 'headphones', 'camera', 
                'earbuds', 'powerbank', 'smartwatch', 'calculator', 'usb', 'cable',
                'mouse', 'keyboard', 'speaker', 'adapter', 'battery',
                'computer', 'monitor', 'printer', 'scanner', 'router', 'modem',
                'television', 'tv', 'remote', 'controller', 'console', 'playstation',
                'xbox', 'nintendo', 'projector', 'webcam', 'microphone', 'mixer'
            ],
            'books': [
                'book', 'notebook', 'textbook', 'diary', 'novel', 'magazine',
                'journal', 'dictionary', 'encyclopedia', 'manual', 'guidebook',
                'textbook', 'comic', 'manga', 'hardcover', 'paperback', 'bible',
                'quran', 'scripture', 'fiction', 'nonfiction', 'biography', 'autobiography'
            ],
            'clothing': [
                'shirt', 'pants', 'jacket', 'hat', 'shoes', 'dress', 't-shirt', 
                'jeans', 'sweater', 'hoodie', 'shorts', 'skirt', 'coat', 'socks',
                'underwear', 'tie', 'scarf', 'gloves', 'suit', 'blazer', 'vest',
                'boots', 'sandals', 'slippers', 'flipflops', 'heels', 'pumps',
                'bra', 'panties', 'boxers', 'briefs', 'stockings', 'tights'
            ],
            'accessories': [
                'wallet', 'keys', 'bag', 'backpack', 'watch', 'jewelry', 
                'sunglasses', 'belt', 'purse', 'handbag', 'lanyard', 'keychain',
                'umbrella', 'cane', 'walking stick', 'tie clip', 'cufflinks',
                'pocket square', 'handkerchief', 'hairpin', 'hairband', 'scrunchy'
            ],
            'documents': [
                'id', 'passport', 'license', 'card', 'certificate', 'document',
                'folder', 'file', 'paper', 'notebook', 'diploma', 'receipt',
                'contract', 'agreement', 'deed', 'will', 'testament', 'invoice',
                'bill', 'statement', 'report', 'thesis', 'dissertation'
            ],
            'sports': [
                'ball', 'racket', 'equipment', 'bottle', 'gloves', 'shoes',
                'bat', 'helmet', 'jersey', 'trainers', 'goggles', 'fins',
                'skates', 'stick', 'dumbbell', 'yoga mat', 'football', 'basketball',
                'baseball', 'soccer', 'tennis', 'golf', 'hockey', 'cricket',
                'volleyball', 'badminton', 'swimming', 'surfing', 'skateboard'
            ],
            'stationery': [
                'pen', 'pencil', 'notebook', 'marker', 'eraser', 'ruler',
                'sharpener', 'stapler', 'scissors', 'glue', 'tape', 'clip',
                'highlighter', 'calculator', 'folder', 'binder', 'envelope',
                'stamp', 'ink', 'cartridge', 'notepad', 'postit', 'post-it'
            ],
            'toys': [
                'toy', 'game', 'stuffed', 'doll', 'car', 'action figure',
                'puzzle', 'lego', 'board game', 'cards', 'dice', 'puzzle',
                'teddy', 'bear', 'robot', 'transformers', 'kite', 'frisbee',
                'water gun', 'nerf', 'plush', 'figurine', 'model kit'
            ],
            'kitchen': [
                'bottle', 'container', 'utensil', 'lunchbox', 'thermos',
                'cup', 'plate', 'bowl', 'cutlery', 'knife', 'spoon', 'fork',
                'tupperware', 'flask', 'food container', 'pan', 'pot', 'skillet',
                'wok', 'ladle', 'spatula', 'whisk', 'grater', 'peeler', 'can opener'
            ],
            'personal_care': [
                'brush', 'comb', 'cosmetic', 'perfume', 'deodorant',
                'toothbrush', 'toothpaste', 'soap', 'shampoo', 'conditioner',
                'lotion', 'cream', 'makeup', 'razor', 'mirror', 'towel',
                'nail clipper', 'tweezers', 'q-tip', 'cotton', 'tissue', 'napkin'
            ],
            'jewelry': [
                'ring', 'necklace', 'bracelet', 'earrings', 'pendant',
                'chain', 'brooch', 'anklet', 'cufflinks', 'tiara', 'charm',
                'bangle', 'watch', 'timepiece', 'diamond', 'gold', 'silver',
                'platinum', 'pearl', 'ruby', 'sapphire', 'emerald'
            ],
            'bags': [
                'backpack', 'purse', 'handbag', 'briefcase', 'suitcase',
                'duffel', 'tote', 'messenger', 'clutch', 'wallet',
                'satchel', 'crossbody', 'fanny pack', 'waist bag', 'luggage',
                'trunk', 'chest', 'carryon', 'carry-on', 'garment bag'
            ],
            'school_supplies': [
                'backpack', 'notebook', 'binder', 'textbook', 'calculator',
                'pencil case', 'ruler', 'protractor', 'compass', 'locker',
                'backpack', 'lunchbox', 'water bottle', 'glue stick', 'crayons',
                'markers', 'colored pencils', 'highlighters', 'index cards'
            ],
            'musical_instruments': [
                'guitar', 'piano', 'violin', 'flute', 'drum', 'trumpet',
                'saxophone', 'harmonica', 'ukulele', 'keyboard', 'viola',
                'cello', 'bass', 'clarinet', 'oboe', 'bassoon', 'trombone',
                'tuba', 'harp', 'mandolin', 'banjo', 'accordion'
            ],
            'tools': [
                'hammer', 'screwdriver', 'wrench', 'pliers', 'tape measure',
                'drill', 'saw', 'knife', 'multitool', 'flashlight', 'ladder',
                'level', 'chisel', 'mallet', 'vise', 'clamp', 'anvil', 'file',
                'sander', 'grinder', 'welder', 'torch', 'blower'
            ],
            'automotive': [
                'car', 'keys', 'remote', 'tire', 'wheel', 'jack', 'spare',
                'gas', 'fuel', 'oil', 'filter', 'battery', 'jumper', 'cables',
                'toolkit', 'manual', 'gps', 'navigation', 'dashcam', 'camera'
            ],
            'medical': [
                'medicine', 'pill', 'tablet', 'capsule', 'syringe', 'needle',
                'bandage', 'bandaid', 'gauze', 'ointment', 'cream', 'thermometer',
                'mask', 'gloves', 'stethoscope', 'blood pressure', 'monitor'
            ],
            'office': [
                'desk', 'chair', 'lamp', 'monitor', 'keyboard', 'mouse',
                'printer', 'scanner', 'copier', 'fax', 'phone', 'headset',
                'whiteboard', 'bulletin', 'calendar', 'planner', 'organizer'
            ],
            'pet_supplies': [
                'leash', 'collar', 'food', 'bowl', 'toy', 'bed', 'cage',
                'carrier', 'litter', 'box', 'scratch', 'post', 'treat',
                'bone', 'chew', 'brush', 'grooming', 'shampoo'
            ],
            'other': ['miscellaneous', 'unknown', 'unidentified', 'general', 'common']
        }
        
        # Category priority for text detection
        self.category_priority = [
            'electronics', 'jewelry', 'documents', 'bags', 
            'clothing', 'accessories', 'books', 'sports',
            'stationery', 'toys', 'kitchen', 'personal_care',
            'school_supplies', 'musical_instruments', 'tools',
            'automotive', 'medical', 'office', 'pet_supplies'
        ]
        
        # Visual characteristics for each category
        self.visual_profiles = self._create_visual_profiles()
    
    def _create_visual_profiles(self):
        """Create visual profiles for heuristic image analysis"""
        return {
            'electronics': {
                'aspect_ratios': [16/9, 4/3, 16/10, 3/2, 1, 2/1],
                'min_edge_density': 0.08,
                'max_edge_density': 0.3,
                'common_colors': ['black', 'gray', 'silver', 'white', 'blue'],
                'size_range': (100, 1000)  # Typical electronics size in pixels
            },
            'books': {
                'aspect_ratios': [1.2, 1.5, 2.0, 2.5, 3.0],
                'min_edge_density': 0.05,
                'paper_like': True,
                'common_colors': ['white', 'beige', 'brown', 'black', 'red', 'blue', 'green'],
                'texture': 'flat'
            },
            'clothing': {
                'aspect_ratios': [0.5, 0.75, 1, 1.5, 2],
                'color_variance_min': 100,
                'texture_variance_min': 50,
                'common_materials': ['cotton', 'denim', 'wool', 'polyester', 'silk'],
                'flexible_shape': True
            },
            'jewelry': {
                'aspect_ratios': [1, 1.5, 2],
                'min_brightness': 150,
                'small_size': True,
                'max_size': 300,
                'common_colors': ['gold', 'silver', 'white', 'diamond', 'colorful'],
                'reflective': True
            },
            'bags': {
                'aspect_ratios': [0.5, 0.75, 1, 1.25, 1.5, 2],
                'has_straps': True,
                'common_materials': ['leather', 'canvas', 'nylon', 'polyester'],
                'handle_detection': True
            },
            'documents': {
                'aspect_ratios': [0.7, 1, 1.4, 1.618],  # Golden ratio
                'paper_like': True,
                'min_whiteness': 100,
                'max_color_variance': 1000,
                'text_present': True
            }
        }
    
    def detect_category(self, image_path=None, title="", description=""):
        """Detect category from image and text with priority on text analysis"""
        text_data = f"{title} {description}".lower().strip()
        
        # First, try text-based detection (most reliable)
        if text_data:
            text_category = self._detect_from_text(text_data)
            if text_category and text_category != 'other':
                return text_category
        
        # If text detection fails or no text, try image analysis
        if image_path and os.path.exists(image_path):
            image_category = self._detect_from_image(image_path)
            if image_category and image_category != 'other':
                return image_category
        
        return 'other'
    
    def _detect_from_text(self, text):
        """Enhanced text-based category detection with confidence scoring"""
        category_scores = {}
        
        # Clean and tokenize text
        words = text.split()
        
        # Check each category
        for category, keywords in self.categories.items():
            if category == 'other':
                continue
                
            score = 0
            # Check for exact matches first
            for keyword in keywords:
                if f' {keyword} ' in f' {text} ':
                    score += 2  # Exact match bonus
                elif keyword in text:
                    score += 1
            
            # Check for partial matches
            for keyword in keywords:
                for word in words:
                    if keyword in word or word in keyword:
                        score += 0.5
            
            if score > 0:
                category_scores[category] = score
        
        # Return highest scoring category, considering priority
        if category_scores:
            # Apply priority multiplier
            for i, category in enumerate(self.category_priority):
                if category in category_scores:
                    priority_multiplier = 1.0 + (len(self.category_priority) - i) * 0.1
                    category_scores[category] *= priority_multiplier
            
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    def _detect_from_image(self, image_path):
        """Manual/rule-based image analysis without ML"""
        try:
            # Load image
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            img_array = np.array(image)
            
            # Multiple analysis methods
            analysis_results = []
            
            # 1. Heuristic analysis
            heuristic_result = self._heuristic_image_analysis(img_array)
            if heuristic_result:
                analysis_results.append(heuristic_result)
            
            # 2. Color-based analysis
            color_result = self._color_based_analysis(img_array)
            if color_result:
                analysis_results.append(color_result)
            
            # 3. Shape-based analysis
            shape_result = self._shape_based_analysis(img_array)
            if shape_result:
                analysis_results.append(shape_result)
            
            # 4. Texture-based analysis
            texture_result = self._texture_based_analysis(img_array)
            if texture_result:
                analysis_results.append(texture_result)
            
            # Determine final category based on consensus
            if analysis_results:
                return self._get_category_consensus(analysis_results)
                
        except Exception as e:
            print(f"Image analysis error: {e}")
        
        return 'other'
    
    def _heuristic_image_analysis(self, img_array):
        """Enhanced heuristic image analysis based on visual profiles"""
        h, w, _ = img_array.shape
        
        # Calculate basic image properties
        aspect_ratio = w / h
        edge_density = self._calculate_edge_density(img_array)
        brightness = self._calculate_brightness(img_array)
        color_variance = self._calculate_color_variance(img_array)
        
        # Check against each visual profile
        scores = {}
        
        for category, profile in self.visual_profiles.items():
            score = 0
            
            # Aspect ratio matching
            if 'aspect_ratios' in profile:
                for target_ratio in profile['aspect_ratios']:
                    if abs(aspect_ratio - target_ratio) < 0.3:
                        score += 1
            
            # Edge density check
            if 'min_edge_density' in profile and 'max_edge_density' in profile:
                if profile['min_edge_density'] <= edge_density <= profile['max_edge_density']:
                    score += 1
            
            # Brightness check
            if 'min_brightness' in profile:
                if brightness >= profile['min_brightness']:
                    score += 1
            
            # Color variance check
            if 'max_color_variance' in profile:
                if color_variance <= profile['max_color_variance']:
                    score += 1
            elif 'color_variance_min' in profile:
                if color_variance >= profile['color_variance_min']:
                    score += 1
            
            # Size check
            if 'small_size' in profile and profile['small_size']:
                if w < 300 and h < 300:
                    score += 1
            if 'size_range' in profile:
                min_size, max_size = profile['size_range']
                if min_size <= w <= max_size and min_size <= h <= max_size:
                    score += 1
            
            scores[category] = score
        
        # Return best matching category
        if scores:
            best_category = max(scores.items(), key=lambda x: x[1])
            if best_category[1] > 1:  # At least 2 matching criteria
                return best_category[0]
        
        return None
    
    def _color_based_analysis(self, img_array):
        """Analyze category based on dominant colors"""
        # Calculate average color
        avg_color = np.mean(img_array, axis=(0, 1))
        avg_hue = self._rgb_to_hue(avg_color)
        
        # Determine color family
        if avg_hue < 30 or avg_hue > 330:  # Reds
            likely_categories = ['clothing', 'accessories', 'toys']
        elif 30 <= avg_hue < 90:  # Yellows/Oranges
            likely_categories = ['clothing', 'toys', 'personal_care']
        elif 90 <= avg_hue < 150:  # Greens
            likely_categories = ['clothing', 'sports', 'stationery']
        elif 150 <= avg_hue < 210:  # Cyans
            likely_categories = ['electronics', 'clothing']
        elif 210 <= avg_hue < 270:  # Blues
            likely_categories = ['electronics', 'clothing', 'documents']
        elif 270 <= avg_hue < 330:  # Magentas/Purples
            likely_categories = ['clothing', 'accessories', 'jewelry']
        else:
            likely_categories = ['other']
        
        # Check for specific color patterns
        if np.mean(avg_color) > 200:  # Very bright/white
            if np.std(avg_color) < 30:  # Mostly white/gray
                return 'documents'
        
        if np.mean(avg_color) < 50:  # Very dark
            if np.std(avg_color) < 30:  # Mostly black/gray
                return 'electronics'
        
        return likely_categories[0] if likely_categories else None
    
    def _shape_based_analysis(self, img_array):
        """Analyze category based on shape characteristics"""
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Detect contours
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Get largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        perimeter = cv2.arcLength(largest_contour, True)
        
        # Calculate shape compactness
        if perimeter > 0:
            compactness = (4 * np.pi * area) / (perimeter ** 2)
            
            if compactness > 0.8:  # Circle-like
                return 'jewelry' if area < 50000 else 'sports'
            elif 0.6 < compactness <= 0.8:  # Square-like
                return 'electronics' if area < 100000 else 'books'
            else:  # Rectangular or irregular
                if area > 100000:  # Large
                    return 'clothing' if perimeter/area < 0.01 else 'bags'
                else:  # Small
                    return 'accessories' if perimeter/area < 0.02 else 'tools'
        
        return None
    
    def _texture_based_analysis(self, img_array):
        """Analyze category based on texture"""
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Calculate texture metrics
        texture_score = self._calculate_texture_score(gray)
        smoothness = self._calculate_smoothness(gray)
        
        if texture_score > 50:
            if smoothness > 0.8:
                return 'electronics'  # Smooth and textured (buttons, screens)
            else:
                return 'clothing'  # Textured fabric
        elif smoothness > 0.9:
            return 'documents'  # Very smooth
        elif smoothness < 0.3:
            return 'tools'  # Rough surface
        
        return None
    
    def _calculate_edge_density(self, img_array):
        """Calculate edge density in image"""
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return np.sum(edges > 0) / (gray.shape[0] * gray.shape[1])
    
    def _calculate_brightness(self, img_array):
        """Calculate average brightness"""
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        return np.mean(hsv[:,:,2])
    
    def _calculate_color_variance(self, img_array):
        """Calculate color variance"""
        return np.var(img_array, axis=(0, 1)).mean()
    
    def _rgb_to_hue(self, rgb_color):
        """Convert RGB color to hue value"""
        r, g, b = rgb_color / 255.0
        cmax = max(r, g, b)
        cmin = min(r, g, b)
        delta = cmax - cmin
        
        if delta == 0:
            hue = 0
        elif cmax == r:
            hue = 60 * (((g - b) / delta) % 6)
        elif cmax == g:
            hue = 60 * (((b - r) / delta) + 2)
        else:  # cmax == b
            hue = 60 * (((r - g) / delta) + 4)
        
        return hue
    
    def _calculate_texture_score(self, gray_image):
        """Calculate texture score using gradient magnitude"""
        sobelx = cv2.Sobel(gray_image, cv2.CV_64F, 1, 0, ksize=5)
        sobely = cv2.Sobel(gray_image, cv2.CV_64F, 0, 1, ksize=5)
        gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
        return np.mean(gradient_magnitude)
    
    def _calculate_smoothness(self, gray_image):
        """Calculate smoothness score"""
        # Calculate local variance
        kernel = np.ones((5,5), np.float32)/25
        smoothed = cv2.filter2D(gray_image, -1, kernel)
        variance = np.var(gray_image - smoothed)
        
        # Normalize to 0-1 range
        max_variance = 1000  # Adjust based on typical values
        smoothness = 1 - min(variance / max_variance, 1)
        return smoothness
    
    def _get_category_consensus(self, results):
        """Get consensus from multiple analysis results"""
        from collections import Counter
        
        # Count occurrences
        result_counts = Counter(results)
        
        # Find most common result
        most_common = result_counts.most_common(1)
        
        if most_common:
            category, count = most_common[0]
            if count >= 2:  # At least two methods agree
                return category
        
        # If no consensus, return first non-'other' result
        for result in results:
            if result != 'other':
                return result
        
        return 'other'

# Helper functions for Django integration
def detect_category_from_image(instance, image_field):
    """Helper function to detect category from image"""
    if image_field and hasattr(image_field, 'path'):
        detector = PracticalCategoryDetector()
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

def batch_categorize_items(items):
    """Batch categorize multiple items efficiently"""
    detector = PracticalCategoryDetector()
    categorized_count = 0
    
    for item in items:
        if hasattr(item, 'item_image') and item.item_image:
            category = detector.detect_category(
                item.item_image.path if hasattr(item.item_image, 'path') else None,
                getattr(item, 'title', ''),
                getattr(item, 'description', '')
            )
            
            if category and category != 'other':
                from .models import Category
                category_obj, _ = Category.objects.get_or_create(
                    name=category.capitalize(),
                    defaults={'description': f'Auto-detected {category} category'}
                )
                item.category = category_obj
                item.save()
                categorized_count += 1
    
    return categorized_count

def get_category_suggestions(text, image_path=None):
    """Get multiple category suggestions with confidence scores"""
    detector = PracticalCategoryDetector()
    
    if not text and not image_path:
        return []
    
    suggestions = {}
    
    # Text-based suggestions
    if text:
        words = text.lower().split()
        for category, keywords in detector.categories.items():
            if category == 'other':
                continue
            matches = sum(1 for keyword in keywords if any(keyword in word or word in keyword for word in words))
            if matches > 0:
                suggestions[category] = suggestions.get(category, 0) + matches * 2
    
    # Image-based suggestions (if available)
    if image_path and os.path.exists(image_path):
        try:
            image = Image.open(image_path)
            img_array = np.array(image.convert('RGB'))
            
            # Run multiple analyses
            heuristic = detector._heuristic_image_analysis(img_array)
            color = detector._color_based_analysis(img_array)
            shape = detector._shape_based_analysis(img_array)
            texture = detector._texture_based_analysis(img_array)
            
            # Add image analysis results
            for result in [heuristic, color, shape, texture]:
                if result:
                    suggestions[result] = suggestions.get(result, 0) + 1
        except:
            pass
    
    # Sort by confidence score
    sorted_suggestions = sorted(suggestions.items(), key=lambda x: x[1], reverse=True)
    
    return [cat for cat, score in sorted_suggestions[:3]]  # Top 3 suggestions