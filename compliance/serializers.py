

# from rest_framework import serializers
# from compliance.models import KycProfile, KycDocument


# class KycDocumentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = KycDocument
#         fields = ["id", "doc_type", "file", "uploaded_at"]
#         read_only_fields = ["id", "uploaded_at"]


# class KycProfileSerializer(serializers.ModelSerializer):
#     documents = KycDocumentSerializer(many=True, read_only=True)

#     class Meta:
#         model = KycProfile
#         fields = [
#             "id",
#             "status",
#             "full_name",
#             "phone",
#             "dob",
#             "docType",
#             "docNum",
#             "submitted_at",
#             "reviewed_at",
#             "approved_at",
#             "review_note",
#             "rejected_reason",
#             "documents",
#         ]
#         read_only_fields = [
#             "id",
#             "status",
#             "submitted_at",
#             "reviewed_at",
#             "approved_at",
#             "review_note",
#             "rejected_reason",
#         ]