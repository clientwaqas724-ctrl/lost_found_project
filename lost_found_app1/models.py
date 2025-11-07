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
##$$$$$$$$$$$$$$$$$$$$$$$############################################################
import numpy as np
# from io import BytesIO
# from PIL import Image
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
# from tensorflow.keras.preprocessing import image as keras_image
# from tensorflow.keras.models import Model

######################################################################################################################################################
######################################################################################################################################################
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
        Fixed save method that doesn't break superuser permissions
        """
        # If user is already a superuser (created via createsuperuser), preserve that
        if self.is_superuser:
            # Superuser should always have admin privileges
            self.user_type = 'admin'
            self.is_staff = True
            self.is_active = True
        else:
            # For regular users, set permissions based on user_type
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
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', self.profile_image.url)
        return "No Image"
    profile_image_preview.short_description = 'Profile Image'
######################################################################################################################################################
######################################################################################################################################################
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

######################################################################################################################################################
######################################################################################################################################################
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
    
    # Manual image search fields
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
    # Image handling
    item_image = models.ImageField(upload_to='lost_items/', blank=True, null=True)    
    # Status and tracking
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
        # Generate search tags automatically if not provided
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
    
    def get_search_tags_list(self):
        """Return search tags as list"""
        return [tag.strip() for tag in self.search_tags.split(',') if tag.strip()]
    
    def get_color_tags_list(self):
        """Return color tags as list"""
        return [tag.strip() for tag in self.color_tags.split(',') if tag.strip()]
    
    def get_material_tags_list(self):
        """Return material tags as list"""
        return [tag.strip() for tag in self.material_tags.split(',') if tag.strip()]
######################################################################################################################################################
######################################################################################################################################################
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
######################################################################################################################################################
######################################################################################################################################################
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
######################################################################################################################################################
######################################################################################################################################################
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

######################################################################################################################################################
######################################################################################################################################################
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
#############################################################################################################################
# # Preload MobileNetV2 model once (lightweight feature extractor)
# mobilenet_model = MobileNetV2(weights='imagenet', include_top=False, pooling='avg')

# class ImageFeature(models.Model):
#     """
#     Stores precomputed embeddings (feature vectors) for each item image
#     to enable image-based search.
#     """
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     item_type = models.CharField(max_length=10, choices=(('lost', 'Lost'), ('found', 'Found')))
#     item_id = models.UUIDField()
#     embedding = models.BinaryField()  # Serialized NumPy vector
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.item_type.title()} Item Feature ({self.item_id})"


# def generate_image_embedding(img_file):
#     """
#     Generates a normalized feature vector (embedding) from an image using MobileNetV2.
#     """
#     try:
#         img = Image.open(img_file).convert("RGB")
#         img = img.resize((224, 224))
#         x = keras_image.img_to_array(img)
#         x = np.expand_dims(x, axis=0)
#         x = preprocess_input(x)
#         features = mobilenet_model.predict(x)[0]
#         features = features / np.linalg.norm(features)  # Normalize vector
#         return features.tobytes()
#     except Exception as e:
#         print("Embedding generation error:", e)
#         return None


# # === Auto-generate embeddings when LostItem or FoundItem is saved ===

# @receiver(post_save, sender='lost_found_app1.LostItem')  # replace 'yourapp' with actual app name
# def create_lost_item_embedding(sender, instance, **kwargs):
#     if instance.item_image:
#         emb = generate_image_embedding(instance.item_image)
#         if emb:
#             ImageFeature.objects.update_or_create(
#                 item_type='lost',
#                 item_id=instance.id,
#                 defaults={'embedding': emb}
#             )

# @receiver(post_save, sender='lost_found_app1.FoundItem')
# def create_found_item_embedding(sender, instance, **kwargs):
#     if instance.item_image:
#         emb = generate_image_embedding(instance.item_image)
#         if emb:
#             ImageFeature.objects.update_or_create(
#                 item_type='found',
#                 item_id=instance.id,
#                 defaults={'embedding': emb}
#             )
