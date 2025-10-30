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

