from django import forms
from api.models import Product, Category,ProductVariant

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'brand', 'model_name', 'short_description', 'description', 
                 'specifications', 'key_features', 'category', 'subcategory', 'price', 
                 'discount_price', 'mrp', 'stock', 'minimum_order_quantity', 
                 'maximum_order_quantity', 'sku', 'barcode', 'hsn_code', 'weight', 
                 'dimensions_length', 'dimensions_width', 'dimensions_height', 
                 'condition', 'availability_status', 'meta_title', 'meta_description', 
                 'tags', 'is_free_shipping', 'delivery_time_min', 'delivery_time_max', 
                 'is_active', 'is_featured', 'is_bestseller', 'is_new_arrival', 
                 'is_trending', 'is_deal_of_day', 'is_returnable', 'is_replaceable', 
                 'is_cod_available', 'warranty_period', 'warranty_type', 
                 'warranty_description', 'return_period', 'return_policy']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'model_name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_description': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'specifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter JSON format specifications'}),
            'key_features': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter JSON array of features'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'subcategory': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'mrp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'minimum_order_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'maximum_order_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'hsn_code': forms.TextInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dimensions_length': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dimensions_width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dimensions_height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'availability_status': forms.Select(attrs={'class': 'form-control'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'tags': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter JSON array of tags'}),
            'delivery_time_min': forms.NumberInput(attrs={'class': 'form-control'}),
            'delivery_time_max': forms.NumberInput(attrs={'class': 'form-control'}),
            'warranty_period': forms.TextInput(attrs={'class': 'form-control'}),
            'warranty_type': forms.TextInput(attrs={'class': 'form-control'}),
            'warranty_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'return_period': forms.NumberInput(attrs={'class': 'form-control'}),
            'return_policy': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_bestseller': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_new_arrival': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_trending': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_deal_of_day': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_free_shipping': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_returnable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_replaceable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_cod_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = [ 'variant_value', 'price', 'discount_price', 'mrp', 
                 'stock', 'sku', 'is_active', 'variant_image', 'hex_color_code', 
                 'size_chart']
        widgets = {
            'variant_type': forms.Select(attrs={'class': 'form-control'}),
            'variant_value': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'mrp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'hex_color_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '#FF0000'}),
            'size_chart': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'additional_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter JSON format'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'variant_image': forms.FileInput(attrs={'class': 'form-control'}),
        }