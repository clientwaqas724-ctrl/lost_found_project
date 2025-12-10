from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Category, LostItem, FoundItem, Claim, Notification, ImageSearchLog, Message
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.base import ContentFile
from urllib.request import urlopen
from urllib.parse import urlparse
import os
import uuid
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import json
###################################################################################################################################################################################################
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
        password = validated_data.pop('password')
        validated_data.pop('password2', None)
        profile_image_data = validated_data.pop('profile_image', None)

        user = User(**validated_data)
        user.set_password(password)

        if isinstance(profile_image_data, str) and profile_image_data.startswith(('http://', 'https://')):
            try:
                response = urlopen(profile_image_data)
                image_content = response.read()
                name = os.path.basename(urlparse(profile_image_data).path)
                if not name:
                    name = f"{uuid.uuid4()}.jpg"
                user.profile_image.save(name, ContentFile(image_content), save=False)
            except Exception as e:
                raise serializers.ValidationError({"profile_image": f"Invalid image URL: {str(e)}"})
        elif profile_image_data:
            user.profile_image = profile_image_data

        user.save()
        return user

###################################################################################################################################################################################################
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

        if not email:
            errors['email'] = ['This field is required.']
        if not password:
            errors['password'] = ['This field is required.']

        if errors:
            raise serializers.ValidationError(errors)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'detail': 'Invalid email or password.'})

        user = authenticate(username=user.username, password=password)
        if not user:
            raise serializers.ValidationError({'detail': 'Invalid email or password.'})

        refresh = RefreshToken.for_user(user)
        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

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

###################################################################################################################################################################################################
class UserProfileSerializer(serializers.ModelSerializer):
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
        profile_image = validated_data.pop('profile_image', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if profile_image is not None:
            instance.profile_image = profile_image
        
        instance.save()
        return instance

###################################################################################################################################################################################################
class UpdatePasswordSerializer(serializers.Serializer):
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

###################################################################################################################################################################################################
class ForgotPasswordSerializer(serializers.Serializer):
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

###################################################################################################################################################################################################
class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'user_type', 'phone_number', 'tower_number', 'room_number',
            'profile_image', 'date_joined', 'is_active'
        )
        read_only_fields = fields

###################################################################################################################################################################################################
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']

###################################################################################################################################################################################################
class FlexibleCategoryField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        from django.core.exceptions import ObjectDoesNotExist
        
        if isinstance(data, int) or (isinstance(data, str) and data.isdigit()):
            try:
                return Category.objects.get(pk=int(data))
            except Category.DoesNotExist:
                raise serializers.ValidationError(f"Category with id {data} does not exist.")
        elif isinstance(data, str):
            try:
                return Category.objects.get(name=data)
            except Category.DoesNotExist:
                raise serializers.ValidationError(f"Category with name '{data}' does not exist.")
        else:
            raise serializers.ValidationError("Invalid category format. Must be ID or name.")

###################################################################################################################################################################################################
class LostItemSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    search_tags_list = serializers.SerializerMethodField()
    color_tags_list = serializers.SerializerMethodField()
    material_tags_list = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = LostItem
        fields = [
            'id', 'user', 'title', 'description', 'category', 'category_name',
            'search_tags', 'search_tags_list', 'color_tags', 'color_tags_list',
            'material_tags', 'material_tags_list', 'lost_location', 'lost_date', 
            'lost_time', 'brand', 'color', 'size', 'item_image', 'image_url',
            'status', 'is_verified', 'created_at', 'updated_at'
        ]

    def get_search_tags_list(self, obj):
        return [tag.strip() for tag in obj.search_tags.split(',')] if obj.search_tags else []

    def get_color_tags_list(self, obj):
        return [tag.strip() for tag in obj.color_tags.split(',')] if obj.color_tags else []

    def get_material_tags_list(self, obj):
        return [tag.strip() for tag in obj.material_tags.split(',')] if obj.material_tags else []

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.item_image and request:
            return request.build_absolute_uri(obj.item_image.url)
        elif obj.item_image:
            # Fallback without request context
            return obj.item_image.url
        return None

###################################################################################################################################################################################################
class FoundItemSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    search_tags_list = serializers.SerializerMethodField()
    color_tags_list = serializers.SerializerMethodField()
    material_tags_list = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = FoundItem
        fields = [
            'id', 'user', 'title', 'description', 'category', 'category_name',
            'search_tags', 'search_tags_list', 'color_tags', 'color_tags_list',
            'material_tags', 'material_tags_list', 'found_location', 'found_date', 
            'found_time', 'brand', 'color', 'size', 'item_image', 'image_url',
            'storage_location', 'status', 'is_verified', 'created_at', 'updated_at'
        ]

    def get_search_tags_list(self, obj):
        return [tag.strip() for tag in obj.search_tags.split(',')] if obj.search_tags else []

    def get_color_tags_list(self, obj):
        return [tag.strip() for tag in obj.color_tags.split(',')] if obj.color_tags else []

    def get_material_tags_list(self, obj):
        return [tag.strip() for tag in obj.material_tags.split(',')] if obj.material_tags else []

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.item_image and request:
            return request.build_absolute_uri(obj.item_image.url)
        elif obj.item_image:
            # Fallback without request context
            return obj.item_image.url
        return None

###################################################################################################################################################################################################
class UserItemsSerializer(serializers.Serializer):
    lost_items = serializers.SerializerMethodField()
    found_items = serializers.SerializerMethodField()

    def get_lost_items(self, obj):
        lost_items = LostItem.objects.filter(user=obj)
        # Pass the context from parent serializer to child serializer
        return LostItemSerializer(lost_items, many=True, context=self.context).data

    def get_found_items(self, obj):
        found_items = FoundItem.objects.filter(user=obj)
        # Pass the context from parent serializer to child serializer
        return FoundItemSerializer(found_items, many=True, context=self.context).data

###################################################################################################################################################################################################
###################################################################################################################################################################################################
class ClaimSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField(read_only=True)
    found_item_info = serializers.SerializerMethodField(read_only=True)
    supporting_images_list = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Claim
        fields = [
            "id",
            "user",
            "user_info",
            "foundItem",
            "found_item_info",
            "claimDescription",
            "proofOfOwnership",
            "supportingImages",
            "supporting_images_list",
            "status",
            "adminNotes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
        
        # --- FIX: Ensure foundItem is required on input ---
        extra_kwargs = {
            'foundItem': {'required': True}
        }

    def get_user_info(self, obj):
        if not obj.user: return None
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'full_name': obj.user.get_full_name(),
            'phone_number': obj.user.phone_number
        }

    def get_found_item_info(self, obj):
        if not obj.foundItem: return None
            
        return {
            'id': obj.foundItem.id,
            'title': obj.foundItem.title,
            'description': obj.foundItem.description,
            'image_url': obj.foundItem.item_image.url if obj.foundItem.item_image else None,
            'found_location': obj.foundItem.found_location,
            'found_date': obj.foundItem.found_date,
            'status': obj.foundItem.status,
            'user': {
                'id': obj.foundItem.user.id,
                'username': obj.foundItem.user.username,
                'email': obj.foundItem.user.email,
                'full_name': obj.foundItem.user.get_full_name()
            }
        }

    def get_supporting_images_list(self, obj):
        """Return list of supporting images"""
        if obj.supportingImages:
            return [img.strip() for img in obj.supportingImages.split(',') if img.strip()]
        return []

    def validate(self, data):
        """Validate claim data"""
        # Field validation is handled automatically by DRF due to ModelSerializer
        return data

    def create(self, validated_data):
        """
        FIX: Updated create to explicitly use the 'user' and 'foundItem' objects 
        passed from the ViewSet via serializer.save().
        """
        # Pop objects passed from the viewset's serializer.save()
        found_item = validated_data.pop('foundItem') 
        user = validated_data.pop('user')
        
        # Check if user already has a pending claim for this item
        existing_claim = Claim.objects.filter(
            user=user,
            foundItem=found_item,
            status='pending'
        ).exists()
        
        if existing_claim:
            raise serializers.ValidationError({
                "foundItem": "You already have a pending claim for this item."
            })
            
        # Create the claim
        claim = Claim.objects.create(
            user=user,
            foundItem=found_item,
            **validated_data
        )
        
        # --- Notification Logic ---
        Notification.objects.create(
            user=user,
            notification_type='system',
            title='Claim Submitted',
            message=f'Your claim for "{claim.foundItem.title}" has been submitted successfully.',
            claim=claim
        )
        
        admin_users = User.objects.filter(user_type='admin', is_active=True)
        for admin in admin_users:
            Notification.objects.create(
                user=admin,
                notification_type='claim_update',
                title='New Claim Submitted',
                message=f'A new claim has been submitted for "{claim.foundItem.title}" by {user.username}.',
                claim=claim
            )
            
        Notification.objects.create(
            user=found_item.user,
            notification_type='claim_update',
            title='Item Claimed',
            message=f'Your found item "{found_item.title}" has been claimed by {user.username}.',
            claim=claim
        )
        # --- End Notification Logic ---
            
        return claim

    def update(self, instance, validated_data):
        """Update an existing claim"""
        request = self.context.get('request')
        
        # Update the claim
        updated_claim = super().update(instance, validated_data)
        
        # Create notification for status updates
        if 'status' in validated_data and validated_data['status'] != instance.status:
            Notification.objects.create(
                user=updated_claim.user,
                notification_type='claim_update',
                title=f'Claim Status Updated',
                message=f'Your claim for "{updated_claim.foundItem.title}" has been updated to {updated_claim.get_status_display()}.',
                claim=updated_claim
            )
            
            # Also notify the item owner if status changed by admin
            if request and request.user.user_type == 'admin' and validated_data['status'] in ['approved', 'rejected']:
                Notification.objects.create(
                    user=updated_claim.foundItem.user,
                    notification_type='claim_update',
                    title=f'Claim {validated_data["status"].title()}',
                    message=f'Your found item "{updated_claim.foundItem.title}" has a claim that was {validated_data["status"]}.',
                    claim=updated_claim
                )
        
        return updated_claim
###################################################################################################################################################################################################
###################################################################################################################################################################################################
class MessageSerializer(serializers.ModelSerializer):
    sender_info = serializers.SerializerMethodField()
    receiver_info = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'claim', 'sender', 'sender_info', 'receiver', 'receiver_info', 
                 'message', 'is_read', 'created_at']
        read_only_fields = ['id', 'sender', 'receiver', 'created_at']

    def get_sender_info(self, obj):
        return {
            'id': obj.sender.id,
            'username': obj.sender.username,
            'email': obj.sender.email,
            'phone_number': obj.sender.phone_number
        }

    def get_receiver_info(self, obj):
        return {
            'id': obj.receiver.id,
            'username': obj.receiver.username,
            'email': obj.receiver.email,
            'phone_number': obj.receiver.phone_number
        }

    def create(self, validated_data):
        request = self.context.get('request')
        claim = validated_data.get('claim')
        
        if request.user == claim.user:
            receiver = claim.found_item.user
        else:
            receiver = claim.user
        
        validated_data['sender'] = request.user
        validated_data['receiver'] = receiver
        
        message = super().create(validated_data)
        
        Notification.objects.create(
            user=receiver,
            notification_type='system',
            title='New Message',
            message=f'You have a new message from {request.user.username} about claim for "{claim.found_item.title}".',
            claim=claim,
            message_ref=message
        )
        
        return message

###################################################################################################################################################################################################
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'notification_type', 'title', 'message',
            'lost_item', 'found_item', 'claim', 'message_ref', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']

################################################################################################################################################################
class ImageSearchLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageSearchLog
        fields = [
            'id', 'user', 'search_type', 'search_query', 'color_filters',
            'category_filters', 'results_count', 'search_duration', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']

##############################################################################################################################################################
class ManualImageSearchSerializer(serializers.Serializer):
    search_query = serializers.CharField(required=False, allow_blank=True)

    # Changed from ChoiceField → CharField
    search_type = serializers.CharField(required=False, allow_blank=True)

    color_filters = serializers.CharField(required=False, allow_blank=True)
    category_filters = serializers.CharField(required=False, allow_blank=True)
    max_results = serializers.IntegerField(default=50, min_value=1, max_value=100)

    def validate_search_type(self, value):
        """
        FIX:
        - Allow blank, None
        - If invalid text comes (like 'Electronics'), auto-set to None
        """
        if not value or value.strip() == "":
            return None

        value = value.lower().strip()

        if value not in ["lost", "found", "all"]:
            # ❗ Auto-normalize wrong values instead of throwing error
            return None

        return value

##########################################################################################################################################################################
class DashboardStatsSerializer(serializers.Serializer):
    total_lost_items = serializers.IntegerField()
    total_found_items = serializers.IntegerField()
    total_claims = serializers.IntegerField()
    pending_claims = serializers.IntegerField()
    approved_claims = serializers.IntegerField()
    total_users = serializers.IntegerField()
    recent_activities = serializers.ListField()

###################################################################################################################################################################################################
class AdminDashboardStatsSerializer(DashboardStatsSerializer):
    verified_lost_items = serializers.IntegerField()
    verified_found_items = serializers.IntegerField()
    returned_items = serializers.IntegerField()
    claimed_items = serializers.IntegerField()
    user_registrations_today = serializers.IntegerField()





























