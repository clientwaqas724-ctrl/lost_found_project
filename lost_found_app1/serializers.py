from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Category, LostItem, FoundItem, Claim, Notification, ImageSearchLog
from django.core.files.base import ContentFile
from urllib.request import urlopen
from urllib.parse import urlparse
import os
#################################################################################################################################################
#################################################################################################################################################
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    tokens = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password2',
            'first_name',
            'last_name',
            'user_type',
            'phone_number',
            'tower_number',
            'room_number',
            'profile_image',
            'tokens'
        ]

    def get_tokens(self, obj):
        refresh = RefreshToken.for_user(obj)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def validate(self, attrs):
        errors = {}

        # Required fields validation
        required_fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'user_type']
        for field in required_fields:
            if not attrs.get(field):
                errors[field] = ['This field is required.']

        # Check if passwords match
        if attrs.get('password') and attrs.get('password2') and attrs['password'] != attrs['password2']:
            errors['password2'] = ['Passwords do not match.']

        # Check if username/email already exist
        if User.objects.filter(username=attrs.get('username')).exists():
            errors['username'] = ['A user with this username already exists.']

        if User.objects.filter(email=attrs.get('email')).exists():
            errors['email'] = ['A user with this email already exists.']

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        """
        Create a user that accepts:
        - uploaded files,
        - URLs,
        - or existing local filenames (inside MEDIA_ROOT/profile_images/)
        """
        password = validated_data.pop('password')
        validated_data.pop('password2', None)

        profile_image = validated_data.get('profile_image')

        # Handle profile image if provided as string
        if isinstance(profile_image, str):
            # Case 1: Remote URL (http/https)
            if profile_image.startswith(('http://', 'https://')):
                try:
                    response = urlopen(profile_image)
                    file_name = os.path.basename(urlparse(profile_image).path)
                    if not file_name:
                        file_name = f"{uuid.uuid4()}.jpg"
                    validated_data['profile_image'] = ContentFile(response.read(), name=file_name)
                except Exception as e:
                    raise serializers.ValidationError({
                        "profile_image": f"Could not download image from URL: {str(e)}"
                    })

            # Case 2: Local filename (relative to media/profile_images)
            else:
                media_path = os.path.join('media', 'profile_images', profile_image)
                if os.path.exists(media_path):
                    with open(media_path, 'rb') as f:
                        validated_data['profile_image'] = ContentFile(f.read(), name=profile_image)
                else:
                    # File not found, just ignore (user can still register)
                    validated_data['profile_image'] = None

        # If it's an actual uploaded file, Django handles it automatically

        # Create user instance
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
#################################################################################################################################################
#################################################################################################################################################
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    tokens = serializers.SerializerMethodField(read_only=True)
    user = serializers.SerializerMethodField(read_only=True)
    redirect_url = serializers.SerializerMethodField(read_only=True)

    def get_tokens(self, obj):
        return obj.get('tokens', {})

    def get_user(self, obj):
        return obj.get('user', {})

    def get_redirect_url(self, obj):
        return obj.get('redirect_url', '')

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        errors = {}

        # Validation for missing fields
        if not email:
            errors['email'] = ['This field is required.']
        if not password:
            errors['password'] = ['This field is required.']

        if errors:
            raise serializers.ValidationError(errors)

        # Find user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'detail': 'Invalid email or password.'})

        # Authenticate user using username (since Django authenticate uses username)
        user = authenticate(username=user.username, password=password)
        if not user:
            raise serializers.ValidationError({'detail': 'Invalid email or password.'})

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        # Get profile image URL
        profile_image_url = user.profile_image.url if user.profile_image else None

        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.user_type,
            'phone_number': user.phone_number,
            'tower_number': user.tower_number,
            'room_number': user.room_number,
            'profile_image': profile_image_url,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }

        redirect_url = '/admin-dashboard/' if user.user_type == 'admin' else '/resident-dashboard/'

        return {
            'user': user_data,
            'tokens': tokens,
            'redirect_url': redirect_url
        }

#################################################################################################################################################
#################################################################################################################################################
class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for viewing and updating user profile."""
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'user_type',
            'phone_number',
            'tower_number',
            'room_number',
            'profile_image',
            'profile_image_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user_type', 'created_at', 'updated_at', 'username']

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None

    def update(self, instance, validated_data):
        # Handle profile image separately to avoid required field issues
        profile_image = validated_data.pop('profile_image', None)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update profile image if provided
        if profile_image is not None:
            instance.profile_image = profile_image
        
        instance.save()
        return instance

#################################################################################################################################################
#################################################################################################################################################
class UpdatePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password."""
    old_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password], style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        user = self.context['request'].user

        if not user.check_password(attrs.get('old_password')):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})

        if attrs.get('new_password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
#########################################################################
class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users (limited fields for privacy)
    """
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'user_type', 'phone_number', 'tower_number', 'room_number',
            'profile_image', 'date_joined', 'is_active'
        )
        read_only_fields = fields
#################################################################################################################################################
#################################################################################################################################################
#################################################################################################################################################
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']

#################################################################################################################################################
class LostItemSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    search_tags_list = serializers.SerializerMethodField()
    color_tags_list = serializers.SerializerMethodField()
    material_tags_list = serializers.SerializerMethodField()
    item_image = serializers.CharField(required=False, allow_blank=True, allow_null=True)  # accept URL or base64

    class Meta:
        model = LostItem
        fields = [
            'id', 'user', 'title', 'description', 'category', 'category_name',
            'search_tags', 'color_tags', 'material_tags', 'lost_location',
            'lost_date', 'lost_time', 'brand', 'color', 'size', 'item_image',
            'status', 'is_verified', 'created_at', 'updated_at',
            'search_tags_list', 'color_tags_list', 'material_tags_list'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'is_verified']

    def get_search_tags_list(self, obj):
        return obj.get_search_tags_list()

    def get_color_tags_list(self, obj):
        return obj.get_color_tags_list()

    def get_material_tags_list(self, obj):
        return obj.get_material_tags_list()

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        image_data = validated_data.pop('item_image', None)
        instance = LostItem(**validated_data)
        instance.user = user

        # ✅ Handle image URL upload
        if image_data and isinstance(image_data, str) and image_data.startswith("http"):
            try:
                image_name = os.path.basename(urlparse(image_data).path)
                image_content = urlopen(image_data).read()
                instance.item_image.save(image_name, ContentFile(image_content), save=False)
            except Exception as e:
                raise serializers.ValidationError({"item_image": f"Invalid image URL or download failed: {e}"})
        
        # ✅ If file is uploaded normally (multipart/form-data), DRF handles automatically
        instance.save()
        return instance
#################################################################################################################################################
class FoundItemSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    search_tags_list = serializers.SerializerMethodField()
    color_tags_list = serializers.SerializerMethodField()
    material_tags_list = serializers.SerializerMethodField()

    # Support both uploaded image and URL
    image_url = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = FoundItem
        fields = [
            'id', 'user', 'title', 'description', 'category', 'category_name',
            'search_tags', 'color_tags', 'material_tags', 'found_location',
            'found_date', 'found_time', 'brand', 'color', 'size',
            'item_image', 'image_url', 'storage_location', 'status',
            'is_verified', 'created_at', 'updated_at',
            'search_tags_list', 'color_tags_list', 'material_tags_list'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'is_verified']

    def get_search_tags_list(self, obj):
        return obj.get_search_tags_list()

    def get_color_tags_list(self, obj):
        return obj.get_color_tags_list()

    def get_material_tags_list(self, obj):
        return obj.get_material_tags_list()

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
#################################################################################################################################################
class ClaimSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    found_item_title = serializers.CharField(source='found_item.title', read_only=True)
    found_item_image = serializers.ImageField(source='found_item.item_image', read_only=True)

    class Meta:
        model = Claim
        fields = [
            'id', 'user', 'user_email', 'found_item', 'found_item_title', 'found_item_image',
            'claim_description', 'proof_of_ownership', 'supporting_images',
            'status', 'admin_notes', 'created_at', 'updated_at', 'resolved_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'resolved_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

#################################################################################################################################################
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'notification_type', 'title', 'message',
            'lost_item', 'found_item', 'claim', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']

#################################################################################################################################################
class ImageSearchLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageSearchLog
        fields = [
            'id', 'user', 'search_type', 'search_query', 'color_filters',
            'category_filters', 'results_count', 'search_duration', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']

#################################################################################################################################################
class ManualImageSearchSerializer(serializers.Serializer):
    search_query = serializers.CharField(required=True)
    search_type = serializers.ChoiceField(choices=[('lost', 'Lost Items'), ('found', 'Found Items')], required=True)
    color_filters = serializers.CharField(required=False, allow_blank=True)
    category_filters = serializers.CharField(required=False, allow_blank=True)
    max_results = serializers.IntegerField(default=50, min_value=1, max_value=100)

#################################################################################################################################################
class DashboardStatsSerializer(serializers.Serializer):
    total_lost_items = serializers.IntegerField()
    total_found_items = serializers.IntegerField()
    total_claims = serializers.IntegerField()
    pending_claims = serializers.IntegerField()
    approved_claims = serializers.IntegerField()
    total_users = serializers.IntegerField()
    recent_activities = serializers.ListField()

#################################################################################################################################################
class AdminDashboardStatsSerializer(DashboardStatsSerializer):
    verified_lost_items = serializers.IntegerField()
    verified_found_items = serializers.IntegerField()
    returned_items = serializers.IntegerField()
    claimed_items = serializers.IntegerField()

    user_registrations_today = serializers.IntegerField()

