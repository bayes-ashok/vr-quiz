import uuid
from django.db import models
from datetime import datetime

def unique_image_filename(instance, filename):
    # You can use a combination of instance-specific data (e.g., name, key) and UUID to ensure uniqueness
    extension = filename.split('.')[-1]
    # Generate a unique identifier for the file and append the original extension
    unique_filename = f"{instance.key}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{extension}"
    return f"images/{unique_filename}"

class KeyValueData(models.Model):
    key = models.CharField(max_length=255, unique=True)  # Store key as a unique string
    value = models.TextField()  # Store the value as text
    
    # Add a name field
    name = models.CharField(max_length=255)
    
    # Add gender field with choices
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    # Store multiple integers (as a comma-separated string)
    multiple_int_values = models.TextField(blank=True, null=True)  # Example: store as comma-separated string
    
    # Add an image field with unique filename logic
    image = models.ImageField(upload_to=unique_image_filename, blank=True, null=True)  # Store images in the 'images/' folder inside MEDIA_ROOT

    def __str__(self):
        return self.key

# Model to store the API response data
class SurveyResponse(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100, blank=True, null=True)
 # Add gender field with choices
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    selected_options_from_one_to_five = models.TextField(blank=True, null=True)
    selected_options_rest_questions = models.TextField(blank=True, null=True)
    score = models.IntegerField()
    correctly_answered = models.TextField(blank=True, null=True)  # New field for correctness
    skipped = models.BooleanField(default=False)  # New field for skipped status

    def __str__(self):
        return f"SurveyResponse {self.id}"

    class Meta:
        verbose_name = "Survey Response"
        verbose_name_plural = "Survey Responses"