from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    User, Category, LostItem, FoundItem, Claim,
    Notification, ImageSearchLog, Message
)

########################################################################################################################################
# CUSTOM USER ADMIN
########################################################################################################################################
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'email', 'user_type', 'phone_number',
        'tower_number', 'room_number', 'profile_image_preview', 'date_joined'
    )
    list_filter = ('user_type', 'is_staff', 'is_active')
    readonly_fields = ('profile_image_preview',)

    fieldsets = UserAdmin.fieldsets + (
        ('DHUAM Information', {
            'fields': (
                'user_type', 'phone_number', 'tower_number',
                'room_number', 'profile_image', 'profile_image_preview'
            )
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('DHUAM Information', {
            'fields': (
                'user_type', 'phone_number', 'tower_number',
                'room_number', 'profile_image'
            )
        }),
    )

    def profile_image_preview(self, obj):
        return obj.profile_image_preview()

    profile_image_preview.short_description = 'Profile Image'


########################################################################################################################################
# CATEGORY ADMIN
########################################################################################################################################
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    list_per_page = 20


########################################################################################################################################
# LOST ITEM ADMIN
########################################################################################################################################
@admin.register(LostItem)
class LostItemAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'user', 'category', 'status',
        'lost_location', 'lost_date', 'image_preview',
        'created_at'
    )
    list_filter = ('status', 'category', 'lost_date', 'created_at')
    search_fields = (
        'title', 'description', 'lost_location',
        'search_tags', 'color_tags', 'brand'
    )
    readonly_fields = ('created_at', 'updated_at', 'image_preview_large')
    list_per_page = 20

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'description', 'category')
        }),
        ('Manual Search Tags', {
            'fields': ('search_tags', 'color_tags', 'material_tags'),
            'description': 'Tags for manual image-based searching'
        }),
        ('Location & Time', {
            'fields': ('lost_location', 'lost_date', 'lost_time')
        }),
        ('Item Details', {
            'fields': ('brand', 'color', 'size', 'item_image', 'image_preview_large')
        }),
        ('Status', {
            'fields': ('status', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.item_image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                obj.item_image.url
            )
        return "No Image"

    image_preview.short_description = 'Image'

    def image_preview_large(self, obj):
        if obj.item_image:
            return format_html(
                '<img src="{}" width="200" height="200" style="object-fit: cover;" />',
                obj.item_image.url
            )
        return "No Image"

    image_preview_large.short_description = 'Image Preview'


########################################################################################################################################
# FOUND ITEM ADMIN
########################################################################################################################################
@admin.register(FoundItem)
class FoundItemAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'user', 'category', 'status',
        'found_location', 'found_date',
        'image_preview', 'is_verified', 'created_at'
    )
    list_filter = (
        'status', 'category', 'found_date',
        'is_verified', 'created_at'
    )
    search_fields = (
        'title', 'description', 'found_location',
        'brand', 'search_tags', 'color_tags', 'material_tags'
    )
    readonly_fields = (
        'created_at', 'updated_at',
        'image_preview_large', 'auto_generated_tags'
    )
    list_per_page = 20

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'description', 'category')
        }),
        ('Manual Search Tags', {
            'fields': ('search_tags', 'color_tags', 'material_tags', 'auto_generated_tags'),
            'description': 'Used for manual or AI-assisted image-based searching'
        }),
        ('Finding Details', {
            'fields': ('found_location', 'found_date', 'found_time', 'storage_location')
        }),
        ('Item Details', {
            'fields': ('brand', 'color', 'size', 'item_image', 'image_url', 'image_preview_large')
        }),
        ('Status', {
            'fields': ('status', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.item_image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                obj.item_image.url
            )
        if obj.image_url:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                obj.image_url
            )
        return "No Image"

    def image_preview_large(self, obj):
        if obj.item_image:
            return format_html(
                '<img src="{}" width="200" height="200" />',
                obj.item_image.url
            )
        if obj.image_url:
            return format_html(
                '<img src="{}" width="200" height="200" />',
                obj.image_url
            )
        return "No Image"

    def auto_generated_tags(self, obj):
        tags = obj.get_search_tags_list()
        return ", ".join(tags) if tags else "—"

    auto_generated_tags.short_description = 'Auto Generated Tags'


########################################################################################################################################
# CLAIM ADMIN
########################################################################################################################################
@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('user', 'found_item', 'status', 'created_at', 'resolved_at')
    list_filter = ('status', 'created_at', 'resolved_at')
    search_fields = ('user__username', 'found_item__title', 'claimDescription')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20

    fieldsets = (
        ('Claim Information', {
            'fields': ('user', 'found_item', 'claimDescription', 'proof_of_ownership')
        }),
        ('Supporting Evidence', {
            'fields': ('supporting_images',)
        }),
        ('Status & Review', {
            'fields': ('status', 'admin_notes', 'resolved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
########################################################################################################################################
# MESSAGE ADMIN (MISSING IN YOUR VERSION — NOW INCLUDED)
########################################################################################################################################
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('claim', 'sender', 'receiver', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('message', 'sender__username', 'receiver__username')
    readonly_fields = ('created_at',)
    list_per_page = 20


########################################################################################################################################
# NOTIFICATION ADMIN
########################################################################################################################################
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'notification_type', 'title',
        'is_read', 'created_at'
    )
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)
    list_per_page = 20


########################################################################################################################################
# IMAGE SEARCH LOG ADMIN
########################################################################################################################################
@admin.register(ImageSearchLog)
class ImageSearchLogAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'search_type', 'search_query',
        'results_count', 'search_duration', 'created_at'
    )
    list_filter = ('search_type', 'created_at')
    search_fields = ('search_query', 'user__username', 'color_filters')
    readonly_fields = ('created_at',)
    list_per_page = 20

    fieldsets = (
        ('Search Information', {
            'fields': ('user', 'search_type', 'search_query')
        }),
        ('Filters Applied', {
            'fields': ('color_filters', 'category_filters')
        }),
        ('Results', {
            'fields': ('results_count', 'search_duration')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )