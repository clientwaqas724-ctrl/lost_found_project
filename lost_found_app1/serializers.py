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
import uuid
from django.core.files.base import ContentFile
from urllib.parse import urlparse
from urllib.request import urlopen
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

        required_fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'user_type'
        ]
        for field in required_fields:
            if not attrs.get(field):
                errors[field] = ['This field is required.']

        if attrs.get('password') and attrs.get('password2') and attrs['password'] != attrs['password2']:
            errors['password2'] = ['Passwords do not match.']

        if User.objects.filter(username=attrs.get('username')).exists():
            errors['username'] = ['A user with this username already exists.']

        if User.objects.filter(email=attrs.get('email')).exists():
            errors['email'] = ['A user with this email already exists.']

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        """
        Create user instance that supports both:
        - file upload (multipart/form-data)
        - image URL (string)
        """
        password = validated_data.pop('password')
        validated_data.pop('password2', None)

        profile_image_data = validated_data.pop('profile_image', None)

        user = User(**validated_data)
        user.set_password(password)

        # Handle remote image URLs
        if isinstance(profile_image_data, str) and profile_image_data.startswith(('http://', 'https://')):
            try:
                # Open the remote image
                response = urlopen(profile_image_data)
                image_content = response.read()

                # Extract the filename from the URL
                name = os.path.basename(urlparse(profile_image_data).path)
                if not name:  # fallback if URL doesn't have filename
                    name = f"{uuid.uuid4()}.jpg"

                # Save image to the field
                user.profile_image.save(name, ContentFile(image_content), save=False)
            except Exception as e:
                raise serializers.ValidationError({"profile_image": f"Invalid image URL: {str(e)}"})
        elif profile_image_data:
            # If it’s a local uploaded file, DRF will handle it automatically
            user.profile_image = profile_image_data

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

#################(new update the password update code)#################
class UpdatePasswordSerializer(serializers.Serializer):
    """Serializer for updating password using email and old password."""
    email = serializers.EmailField(required=True)
    old_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password], style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "No user found with this email address."})

        if not user.check_password(old_password):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})

        if new_password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
#####################################################################################

#################(new forget the password update code)#################
class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password using email only."""
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password], style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "No user found with this email address."})

        if new_password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
################################################################################################################




###########################################################################################################################################################################
###########################################################################################################################################################################
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
######################################################################################
class FlexibleCategoryField(serializers.PrimaryKeyRelatedField):
    """
    Allows both ID (int) and name (str) to be accepted when setting category.
    """
    def to_internal_value(self, data):
        from django.core.exceptions import ObjectDoesNotExist
        
        if isinstance(data, int) or (isinstance(data, str) and data.isdigit()):
            # Try to treat it as PK
            try:
                return Category.objects.get(pk=int(data))
            except Category.DoesNotExist:
                raise serializers.ValidationError(f"Category with id {data} does not exist.")
        elif isinstance(data, str):
            # Try to treat it as name
            try:
                return Category.objects.get(name=data)
            except Category.DoesNotExist:
                raise serializers.ValidationError(f"Category with name '{data}' does not exist.")
        else:
            raise serializers.ValidationError("Invalid category format. Must be ID or name.")
#################################################################################################################################################
class LostItemSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_info = serializers.SerializerMethodField()  # New field
    
    category = FlexibleCategoryField(queryset=Category.objects.all())
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    search_tags_list = serializers.SerializerMethodField()
    color_tags_list = serializers.SerializerMethodField()
    material_tags_list = serializers.SerializerMethodField()

    item_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = LostItem
        fields = [
            'id', 'user', 'user_info', 'title', 'description', 'category', 'category_name',
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
    
    def get_user_info(self, obj):
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "email": obj.user.email,
            "role": getattr(obj.user, 'user_type', None)
        }

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        image_data = validated_data.get('item_image', None)
        instance = LostItem(**validated_data)
        instance.user = user

        if image_data and isinstance(image_data, str) and image_data.startswith("http"):
            try:
                image_name = os.path.basename(urlparse(image_data).path)
                image_content = urlopen(image_data).read()
                instance.item_image.save(image_name, ContentFile(image_content), save=False)
            except Exception as e:
                raise serializers.ValidationError({"item_image": f"Invalid image URL or download failed: {e}"})

        instance.save()
        return instance
################################################################################################################################################################
class FoundItemSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_info = serializers.SerializerMethodField()  # New field
    category_name = serializers.CharField(source='category.name', read_only=True)
    search_tags_list = serializers.SerializerMethodField()
    color_tags_list = serializers.SerializerMethodField()
    material_tags_list = serializers.SerializerMethodField()

    # Support both uploaded image and URL
    image_url = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = FoundItem
        fields = [
            'id', 'user', 'user_info', 'title', 'description', 'category', 'category_name',
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

    def get_user_info(self, obj):
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "email": obj.user.email,
            "role": getattr(obj.user, 'user_type', None)
        }

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
######################################################################################################################################################################################################
class UserItemsSerializer(serializers.Serializer):
    lost_items = serializers.SerializerMethodField()
    found_items = serializers.SerializerMethodField()
    def get_lost_items(self, obj):
        lost_items = LostItem.objects.filter(user=obj)
        return LostItemSerializer(lost_items, many=True).data
    def get_found_items(self, obj):
        found_items = FoundItem.objects.filter(user=obj)
        return FoundItemSerializer(found_items, many=True).data
##############################################################################################################################################################################################
class ClaimSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    found_item_id = serializers.UUIDField(write_only=True, required=True)
    found_item_title = serializers.CharField(source='found_item.title', read_only=True)
    proof_of_ownership = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = Claim
        fields = [
            'id', 'user', 'found_item_id', 'found_item_title',
            'claim_description', 'proof_of_ownership', 'supporting_images',
            'status', 'admin_notes', 'created_at', 'updated_at', 'resolved_at'
        ]
        read_only_fields = ['id', 'user', 'found_item_title', 'status', 'created_at', 'updated_at', 'resolved_at']

    def create(self, validated_data):
        user = self.context['request'].user
        found_item_id = validated_data.pop('found_item_id')

        # Fetch FoundItem
        try:
            found_item = FoundItem.objects.get(id=found_item_id)
        except FoundItem.DoesNotExist:
            raise serializers.ValidationError({"found_item_id": "Found item does not exist."})

        # Prevent duplicate claims by the same user
        if Claim.objects.filter(user=user, found_item=found_item).exists():
            raise serializers.ValidationError({"detail": "You have already submitted a claim for this item."})

        claim = Claim.objects.create(
            user=user,
            found_item=found_item,
            **validated_data
        )
        return claim
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
    search_query = serializers.CharField(required=False, allow_blank=True)
    search_type = serializers.ChoiceField(
        choices=[('lost', 'Lost Items'), ('found', 'Found Items'), ('all', 'All')],
        required=False,
        allow_blank=True  # ✅ Allows "" without throwing validation error
    )
    color_filters = serializers.CharField(required=False, allow_blank=True)
    category_filters = serializers.CharField(required=False, allow_blank=True)
    max_results = serializers.IntegerField(default=50, min_value=1, max_value=100)

    def validate_search_type(self, value):
        """Normalize blank or None values safely."""
        if value in [None, '', ' ']:
            return None
        return value.lower()
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
######################################################################################################




