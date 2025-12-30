from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Company
from .serializers import CompanySerializer


class MyCompanyView(APIView):
    """Get or update the current user's company (where they are admin)."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        try:
            company = Company.objects.get(admin=request.user)
        except Company.DoesNotExist:
            return Response(
                data={"detail": "No company found for this user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CompanySerializer(company)
        return Response(serializer.data)

    def patch(self, request):
        try:
            company = Company.objects.get(admin=request.user)
        except Company.DoesNotExist:
            return Response(
                {"detail": "No company found for this user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CompanySerializer(company, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
