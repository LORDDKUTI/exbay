# from django.db import models
# from django.conf import settings
# # Create your models here.





# class KycProfile(models.Model):
#     DRAFT = "draft"
#     SUBMITTED = "submitted"
#     APPROVED = "approved"
#     REJECTED = "rejected"

#     STATUS_CHOICES = [
#         (DRAFT, "Draft"),
#         (SUBMITTED, "Submitted"),
#         (APPROVED, "Approved"),
#         (REJECTED, "Rejected"),
#     ]

#     PASSPORT = "passport"
#     NATIONAL_ID = "national_id"
#     DRIVERS_LICENSE = "drivers_license"

#     DOC_TYPE_CHOICES = [
#         (PASSPORT, "Passport"),
#         (NATIONAL_ID, "National ID"),
#         (DRIVERS_LICENSE, "Driver's License"),
#     ]

#     user = models.OneToOneField(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name="kyc",
#     )
#     full_name = models.CharField(max_length=255)
#     phone = models.CharField(max_length=20, blank=True)
#     dob = models.DateField(null=True, blank=True)
#     docType = models.CharField(max_length=50, choices=DOC_TYPE_CHOICES, blank=True)
#     docNum = models.CharField(max_length=100, blank=True)

#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)

#     submitted_at = models.DateTimeField(null=True, blank=True)
#     reviewed_at = models.DateTimeField(null=True, blank=True)
#     approved_at = models.DateTimeField(null=True, blank=True)

#     review_note = models.TextField(blank=True)
#     rejected_reason = models.TextField(blank=True)

#     def __str__(self):
#         return f"KYC {self.user.username} - {self.status}"


# class KycDocument(models.Model):
#     ID_FRONT = "id_front"
#     ID_BACK = "id_back"
#     SELFIE = "selfie"
#     PROOF_OF_ADDRESS = "proof_of_address"

#     DOC_TYPES = [
#         (ID_FRONT, "ID Front"),
#         (ID_BACK, "ID Back"),
#         (SELFIE, "Selfie"),
#         (PROOF_OF_ADDRESS, "Proof of Address"),
#     ]

#     profile = models.ForeignKey(
#         KycProfile,
#         on_delete=models.CASCADE,
#         related_name="documents",
#     )
#     doc_type = models.CharField(max_length=50, choices=DOC_TYPES)
#     file = models.FileField(upload_to="kyc_documents/")
#     uploaded_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.profile.user.username} - {self.doc_type}"