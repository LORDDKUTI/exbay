# from django.shortcuts import render

# # Create your views here.

from django.http import JsonResponse


def compliance_home(request):
    return JsonResponse({"message": "compliance app is working"})

# from django.utils import timezone
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.views import APIView

# from compliance.models import KycProfile, KycDocument
# from compliance.serializers import KycProfileSerializer, KycDocumentSerializer
# from compliance.services import offer_eligible, is_ohio_shipping, kyc_approved


# class OfferEligibilityView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         return Response({
#             "eligible": offer_eligible(request.user),
#             "needs": {
#                 "ohio_shipping": is_ohio_shipping(request.user),
#                 "kyc_approved": kyc_approved(request.user),
#             }
#         })


# class MyKycView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         profile, _ = KycProfile.objects.get_or_create(
#             user=request.user,
#             defaults={"full_name": request.user.get_full_name() or request.user.username},
#         )
#         return Response(KycProfileSerializer(profile).data)

#     def put(self, request):
#         profile, _ = KycProfile.objects.get_or_create(
#             user=request.user,
#             defaults={"full_name": request.user.get_full_name() or request.user.username},
#         )

#         profile.full_name = request.data.get("full_name", profile.full_name)
#         profile.phone = request.data.get("phone", profile.phone)
#         profile.dob = request.data.get("dob", profile.dob)
#         profile.docType = request.data.get("docType", profile.docType)
#         profile.docNum = request.data.get("docNum", profile.docNum)
#         profile.status = KycProfile.SUBMITTED
#         profile.submitted_at = timezone.now()
#         profile.reviewed_at = None
#         profile.review_note = ""
#         profile.rejected_reason = ""
#         profile.approved_at = None
#         profile.save()

#         return Response({"detail": "KYC submitted for review."}, status=status.HTTP_200_OK)


# class MyKycDocumentUploadView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         profile, _ = KycProfile.objects.get_or_create(
#             user=request.user,
#             defaults={"full_name": request.user.get_full_name() or request.user.username},
#         )

#         doc_type = request.data.get("doc_type")
#         file = request.FILES.get("file")

#         if not doc_type:
#             return Response({"detail": "doc_type is required."}, status=status.HTTP_400_BAD_REQUEST)
#         if not file:
#             return Response({"detail": "file is required."}, status=status.HTTP_400_BAD_REQUEST)

#         doc = KycDocument.objects.create(
#             profile=profile,
#             doc_type=doc_type,
#             file=file,
#         )

#         return Response(KycDocumentSerializer(doc).data, status=status.HTTP_201_CREATED)