from rest_framework import serializers
from .models import Category, Transaction, Budget, Investment
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)
    
    class Meta:
        model= User
        fields = ('username', 'email', 'password', 'password2')
        
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']: 
            raise serializers.ValidationError({"password": "Passwords must match."})
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password2') 
        user = User.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include username and password')
        


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'type', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        user = self.context['request'].user
        category_type = self.initial_data.get('type')
        
        # Check for duplicate category name for same user and type
        existing = Category.objects.filter(
            user=user, 
            name__iexact=value, 
            type=category_type
        )
        
        # If updating, exclude current instance
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
            
        if existing.exists():
            raise serializers.ValidationError(f"Category '{value}' already exists for {category_type}")
        
        return value.title()  # Capitalize first letter
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'category', 'type', 'amount', 
            'description', 'date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate(self, attrs):
        # Ensure type matches category.type
        category = attrs.get('category')
        tx_type = attrs.get('type')

        if category and tx_type and category.type != tx_type:
            raise serializers.ValidationError(
                f"Transaction type must match category type ({category.type})."
            )
        return attrs

    def create(self, validated_data):
        # Automatically assign the logged-in user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            self.fields['category'].queryset = Category.objects.filter(user=request.user)
            
class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = [
            'id', 'user', 'category', 'monthly_limit', 
            'month', 'year', 'is_active', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Budget.objects.all(),
                fields=['user', 'category', 'month', 'year'],
                message="A budget for this category, month, and year already exists."
            )
        ]

    def validate_monthly_limit(self, value):
        if value <= 0:
            raise serializers.ValidationError("Monthly limit must be greater than zero.")
        return value

    def create(self, validated_data):
        # Automatically assign the logged-in user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)
    
class InvestmentSerializer(serializers.ModelSerializer):
    profit_loss = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    profit_loss_percentage = serializers.DecimalField(
        max_digits=6, decimal_places=2, read_only=True
    )

    class Meta:
        model = Investment
        fields = [
            'id', 'user', 'name', 'type', 'others',
            'amount_invested', 'current_value', 'quantity',
            'purchase_date', 'created_at', 'updated_at',
            'profit_loss', 'profit_loss_percentage'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'profit_loss', 'profit_loss_percentage']

    def validate(self, attrs):
        # If type is "others", 'others' field must be filled
        inv_type = attrs.get('type')
        others_field = attrs.get('others')

        if inv_type == 'others' and not others_field:
            raise serializers.ValidationError({
                "others": "You must provide details when type is 'others'."
            })

        return attrs

    def create(self, validated_data):
        # Automatically assign logged-in user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)