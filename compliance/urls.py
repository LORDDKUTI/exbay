

# from django.urls import path
# from compliance.views import OfferEligibilityView, MyKycView, MyKycDocumentUploadView

# urlpatterns = [
#     path("offer-eligibility/", OfferEligibilityView.as_view(), name="offer-eligibility"),
#     path("kyc/", MyKycView.as_view(), name="my-kyc"),
#     path("kyc/upload-document/", MyKycDocumentUploadView.as_view(), name="kyc-upload-document"),
# ]


from django.urls import path
from .views import compliance_home

urlpatterns = [
    path("", compliance_home, name="compliance-home"),
]