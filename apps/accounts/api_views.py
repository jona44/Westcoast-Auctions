from rest_framework import generics, permissions
from .serializers import CustomUserSerializer
from .models import User

class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
