from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
import uuid
from datetime import date
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
import uuid
from datetime import date
from django.utils.html import format_html
##########################################################################################################################################################################################################
# import numpy as np
from io import BytesIO
from PIL import Image
from django.db.models.signals import post_save
from django.dispatch import receiver
import os
import hashlib
# from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
# from tensorflow.keras.preprocessing import image as keras_image
# from tensorflow.keras.models import Model
###############################################################################################################################################################################################################
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('resident', 'DHUAM Resident'),
        ('admin', 'Administrator'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='resident')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    tower_number = models.CharField(max_length=10, blank=True, null=True)
    room_number = models.CharField(max_length=10, blank=True, null=True)
    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Preserve superuser permissions and handle remote image URLs.
        """
        # Handle remote URL for profile image if provided
        if isinstance(self.profile_image, str) and self.profile_image.startswith("http"):
            try:
                response = requests.get(self.profile_image)
                if response.status_code == 200:
                    file_name = f"{uuid.uuid4()}.jpg"
                    self.profile_image.save(file_name, ContentFile(response.content), save=False)
            except Exception as e:
                print(f"⚠️ Failed to fetch image from URL: {e}")

        # Superuser logic
        if self.is_superuser:
            self.user_type = 'admin'
            self.is_staff = True
            self.is_active = True
        else:
            if self.user_type == 'admin':
                self.is_staff = True
                self.is_superuser = True
                self.is_active = True
            else:
                self.is_staff = False
                self.is_superuser = False
                self.is_active = True

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"

    def profile_image_preview(self):
        if self.profile_image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                self.profile_image.url
            )
        return "No Image"
    profile_image_preview.short_description = 'Profile Image'
########################################################################################################################################################################################################
#########################################################################################################################################################################################################
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
######################################################################################################################################################################################################
######################################################################################################################################################################################################
class LostItem(models.Model):
    STATUS_CHOICES = (
        ('lost', 'Lost'),
        ('found', 'Found'),
        ('claimed', 'Claimed'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lost_items')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Tags
    search_tags = models.TextField(blank=True, help_text="Comma-separated tags for manual image searching")
    color_tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated color descriptions")
    material_tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated material descriptions")
    
    # Location details
    lost_location = models.CharField(max_length=200)
    lost_date = models.DateField(default=date.today)
    lost_time = models.TimeField(blank=True, null=True)
    
    # Item details
    brand = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=50, blank=True, help_text="Size/dimensions of the item")

    # Image
    item_image = models.ImageField(upload_to='lost_items/', blank=True, null=True)    

    # Status & Verification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lost')
    is_verified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Only generate search_tags if they're empty and we have title
        if not self.search_tags and self.title:
            base_tags = [self.title.lower().strip()]
            if self.brand:
                base_tags.append(self.brand.lower().strip())
            if self.color:
                base_tags.append(self.color.lower().strip())
                if not self.color_tags:
                    self.color_tags = self.color
            if self.category:
                base_tags.append(self.category.name.lower().strip())
            self.search_tags = ", ".join([tag for tag in base_tags if tag])
        
        # Call parent save
        super().save(*args, **kwargs)
    
    def get_search_tags_list(self):
        return [tag.strip() for tag in self.search_tags.split(',') if tag.strip()]
    
    def get_color_tags_list(self):
        return [tag.strip() for tag in self.color_tags.split(',') if tag.strip()]
    
    def get_material_tags_list(self):
        return [tag.strip() for tag in self.material_tags.split(',') if tag.strip()]
#####################################################################################################################################################################################################
####################################################333######################################################################################################################################################
class FoundItem(models.Model):
    STATUS_CHOICES = (
        ('found', 'Found'),
        ('returned', 'Returned'),
        ('disposed', 'Disposed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='found_items')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)

    # Manual search fields
    search_tags = models.TextField(blank=True, help_text="Comma-separated tags for manual image searching")
    color_tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated color descriptions")
    material_tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated material descriptions")

    # Finding details
    found_location = models.CharField(max_length=200)
    found_date = models.DateField(default=date.today)
    found_time = models.TimeField(blank=True, null=True)

    # Item details
    brand = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=50, blank=True, help_text="Size/dimensions of the item")

    # Image handling (supporting both uploads and URLs)
    item_image = models.ImageField(
        upload_to='found_items/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    image_url = models.URLField(blank=True, null=True, help_text="Optional direct URL to image")

    # Storage location
    storage_location = models.CharField(max_length=200, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='found')
    is_verified = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Auto-generate search tags
        if not self.search_tags and self.title:
            base_tags = [self.title.lower()]
            if self.brand:
                base_tags.append(self.brand.lower())
            if self.color:
                base_tags.append(self.color.lower())
                self.color_tags = self.color
            if self.category:
                base_tags.append(self.category.name.lower())
            self.search_tags = ", ".join(base_tags)

        super().save(*args, **kwargs)

    # Utility tag splitters
    def get_search_tags_list(self):
        return [tag.strip() for tag in self.search_tags.split(',') if tag.strip()]

    def get_color_tags_list(self):
        return [tag.strip() for tag in self.color_tags.split(',') if tag.strip()]

    def get_material_tags_list(self):
        return [tag.strip() for tag in self.material_tags.split(',') if tag.strip()]
##########################################################################################################################################################################################################
##########################################################################################################################################################################################################
class Claim(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Item Returned'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claims')
    found_item = models.ForeignKey(FoundItem, on_delete=models.CASCADE, related_name='claims')
    
    # Claim details
    claim_description = models.TextField()
    proof_of_ownership = models.TextField(blank=True)
    supporting_images = models.ImageField(
        upload_to='claim_support/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'found_item']
    
    def __str__(self):
        return f"Claim by {self.user.username} for {self.found_item.title}"
#########################################################################################################################################################################################################
######################################################################################################################################################################################################
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('claim_update', 'Claim Status Update'),
        ('match_found', 'Potential Match Found'),
        ('item_found', 'Your Lost Item Found'),
        ('system', 'System Notification'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Related item (optional)
    lost_item = models.ForeignKey(LostItem, on_delete=models.CASCADE, null=True, blank=True)
    found_item = models.ForeignKey(FoundItem, on_delete=models.CASCADE, null=True, blank=True)
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, null=True, blank=True)
    
    # Read status
    is_read = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} - {self.user.username}"

############################################################################################################################################################################################################
#####################################################################################################################################################################################################
class ImageSearchLog(models.Model):
    """Manual image-based search logging"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    search_type = models.CharField(max_length=20, choices=(('lost', 'Lost Items'), ('found', 'Found Items')))
    search_query = models.TextField(help_text="Search terms used")
    color_filters = models.CharField(max_length=200, blank=True)
    category_filters = models.CharField(max_length=200, blank=True)
    results_count = models.IntegerField(default=0)
    search_duration = models.FloatField(help_text="Search time in seconds")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):

        return f"Image Search - {self.search_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
#######################################################################################################################################################
class ImageFeature(models.Model):
    """
    Stores image fingerprints for similarity search using custom algorithm
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item_type = models.CharField(max_length=10, choices=(('lost', 'Lost'), ('found', 'Found')))
    item_id = models.UUIDField()
    
    # Image metadata for similarity matching
    dominant_colors = models.CharField(max_length=500, blank=True)  # RGB values as string
    color_palette = models.TextField(blank=True)  # Extended color information
    image_size = models.CharField(max_length=50, blank=True)  # Width x Height
    file_size = models.IntegerField(default=0)  # File size in bytes
    aspect_ratio = models.FloatField(default=0.0)
    image_hash = models.CharField(max_length=64, blank=True)  # Perceptual hash
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['item_type', 'item_id']),
            models.Index(fields=['dominant_colors']),
        ]

    def __str__(self):
        return f"{self.item_type.title()} Item Features ({self.item_id})"

def generate_image_fingerprint(img_file):
    """
    Generates a fingerprint for image similarity search using custom algorithm
    """
    try:
        img = Image.open(img_file)
        img = img.convert("RGB")
        
        # Basic image properties
        width, height = img.size
        file_size = img_file.size
        aspect_ratio = width / height if height > 0 else 0
        
        # Generate simple dominant colors (average of quarters)
        img_small = img.resize((4, 4))  # Resize to 4x4 for color analysis
        pixels = list(img_small.getdata())
        
        # Calculate average RGB for the entire image and quarters
        avg_r = sum(p[0] for p in pixels) // len(pixels)
        avg_g = sum(p[1] for p in pixels) // len(pixels)
        avg_b = sum(p[2] for p in pixels) // len(pixels)
        
        dominant_colors = f"{avg_r},{avg_g},{avg_b}"
        
        # Generate simple perceptual hash
        img_gray = img.convert("L").resize((8, 8))  # 8x8 grayscale
        pixels = list(img_gray.getdata())
        avg = sum(pixels) // len(pixels)
        hash_str = ''.join('1' if pixel > avg else '0' for pixel in pixels)
        image_hash = hashlib.md5(hash_str.encode()).hexdigest()
        
        # Extended color palette (top 5 colors)
        color_counts = {}
        for pixel in pixels[:100]:  # Sample first 100 pixels for efficiency
            color_counts[pixel] = color_counts.get(pixel, 0) + 1
        
        top_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        color_palette = ";".join([f"{color[0]}:{color[1]}" for color in top_colors])
        
        return {
            'dominant_colors': dominant_colors,
            'color_palette': color_palette,
            'image_size': f"{width}x{height}",
            'file_size': file_size,
            'aspect_ratio': aspect_ratio,
            'image_hash': image_hash
        }
        
    except Exception as e:
        print(f"Image fingerprint generation error: {e}")
        return None

def find_similar_images(search_image, item_type='both', max_results=10):
    """
    Custom algorithm to find similar images based on image fingerprints
    """
    search_fingerprint = generate_image_fingerprint(search_image)
    if not search_fingerprint:
        return []
    
    results = []
    search_colors = [int(x) for x in search_fingerprint['dominant_colors'].split(',')]
    search_aspect = search_fingerprint['aspect_ratio']
    
    # Determine which item types to search
    if item_type == 'both':
        features = ImageFeature.objects.all()
    else:
        features = ImageFeature.objects.filter(item_type=item_type)
    
    for feature in features:
        score = 0
        
        # Color similarity (40% weight)
        try:
            feature_colors = [int(x) for x in feature.dominant_colors.split(',')]
            color_diff = sum(abs(sc - fc) for sc, fc in zip(search_colors, feature_colors))
            color_score = max(0, 100 - (color_diff / 3))  # Normalize to 0-100
            score += color_score * 0.4
        except:
            pass
        
        # Aspect ratio similarity (30% weight)
        aspect_diff = abs(search_aspect - feature.aspect_ratio)
        aspect_score = max(0, 100 - (aspect_diff * 100))
        score += aspect_score * 0.3
        
        # Size similarity (20% weight)
        try:
            search_w, search_h = map(int, search_fingerprint['image_size'].split('x'))
            feature_w, feature_h = map(int, feature.image_size.split('x'))
            size_diff = abs(search_w - feature_w) + abs(search_h - feature_h)
            size_score = max(0, 100 - (size_diff / 100))  # Normalize
            score += size_score * 0.2
        except:
            pass
        
        # Hash similarity (10% weight) - basic hamming distance
        hash_similarity = sum(c1 == c2 for c1, c2 in zip(
            search_fingerprint['image_hash'], 
            feature.image_hash
        )) / len(search_fingerprint['image_hash']) * 100
        score += hash_similarity * 0.1
        
        if score > 30:  # Minimum similarity threshold
            results.append({
                'item_type': feature.item_type,
                'item_id': feature.item_id,
                'similarity_score': round(score, 2),
                'feature': feature
            })
    
    # Sort by similarity score and return top results
    results.sort(key=lambda x: x['similarity_score'], reverse=True)
    return results[:max_results]

# Signals to generate image fingerprints
@receiver(post_save, sender=LostItem)
def create_lost_item_fingerprint(sender, instance, **kwargs):
    if instance.item_image:
        fingerprint = generate_image_fingerprint(instance.item_image)
        if fingerprint:
            ImageFeature.objects.update_or_create(
                item_type='lost',
                item_id=instance.id,
                defaults=fingerprint
            )

@receiver(post_save, sender=FoundItem)
def create_found_item_fingerprint(sender, instance, **kwargs):
    if instance.item_image:
        fingerprint = generate_image_fingerprint(instance.item_image)
        if fingerprint:
            ImageFeature.objects.update_or_create(
                item_type='found',
                item_id=instance.id,
                defaults=fingerprint
            )
