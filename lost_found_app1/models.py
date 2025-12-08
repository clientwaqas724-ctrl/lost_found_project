from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
import uuid
from datetime import date
from django.utils.html import format_html
####################################################################################################################################################################################################
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
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', self.profile_image.url)
        return "No Image"
    profile_image_preview.short_description = 'Profile Image'
####################################################################################################################################################################################################
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
####################################################################################################################################################################################################
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
    
    search_tags = models.TextField(blank=True, help_text="Comma-separated tags for manual image searching")
    color_tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated color descriptions")
    material_tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated material descriptions")
    
    lost_location = models.CharField(max_length=200)
    lost_date = models.DateField(default=date.today)
    lost_time = models.TimeField(blank=True, null=True)
    
    brand = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=50, blank=True, help_text="Size/dimensions of the item")
    item_image = models.ImageField(upload_to='lost_items/', blank=True, null=True)    
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lost')
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-detect category if not set and image exists
        if not self.category and self.item_image:
            from .category_detector import auto_categorize_item
            auto_categorize_item(self)
        
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
        return [tag.strip() for tag in self.search_tags.split(',') if tag.strip()]
    
    def get_color_tags_list(self):
        return [tag.strip() for tag in self.color_tags.split(',') if tag.strip()]
    
    def get_material_tags_list(self):
        return [tag.strip() for tag in self.material_tags.split(',') if tag.strip()]
####################################################################################################################################################################################################
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

    search_tags = models.TextField(blank=True, help_text="Comma-separated tags for manual image searching")
    color_tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated color descriptions")
    material_tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated material descriptions")

    found_location = models.CharField(max_length=200)
    found_date = models.DateField(default=date.today)
    found_time = models.TimeField(blank=True, null=True)

    brand = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=50, blank=True, help_text="Size/dimensions of the item")

    item_image = models.ImageField(
        upload_to='found_items/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    image_url = models.URLField(blank=True, null=True, help_text="Optional direct URL to image")

    storage_location = models.CharField(max_length=200, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='found')
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Auto-detect category if not set and image exists
        if not self.category and (self.item_image or self.image_url):
            from .category_detector import auto_categorize_item
            auto_categorize_item(self)
        
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
        return [tag.strip() for tag in self.search_tags.split(',') if tag.strip()]

    def get_color_tags_list(self):
        return [tag.strip() for tag in self.color_tags.split(',') if tag.strip()]

    def get_material_tags_list(self):
        return [tag.strip() for tag in self.material_tags.split(',') if tag.strip()]
####################################################################################################################################################################################################
# models.py - Make supporting_images optional
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
    
    claim_description = models.TextField()
    proof_of_ownership = models.TextField(blank=True)
    
    # Make sure it's optional for both null and blank
    supporting_images = models.TextField(blank=True, null=True, default=None)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'found_item']
    
    def __str__(self):
        return f"Claim by {self.user.username} for {self.found_item.title}"
####################################################################################################################################################################################################
class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.username} about {self.claim.found_item.title}"
####################################################################################################################################################################################################
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
    
    lost_item = models.ForeignKey(LostItem, on_delete=models.CASCADE, null=True, blank=True)
    found_item = models.ForeignKey(FoundItem, on_delete=models.CASCADE, null=True, blank=True)
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, null=True, blank=True)
    message_ref = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} - {self.user.username}"
####################################################################################################################################################################################################
class ImageSearchLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    search_type = models.CharField(max_length=20, choices=(('lost', 'Lost Items'), ('found', 'Found Items'), ('all', 'All Items')))
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


