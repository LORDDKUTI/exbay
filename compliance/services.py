
# from accounts.models import Address
# from compliance.models import KycProfile


# def get_default_shipping(user):
#     return Address.objects.filter(
#         user=user,
#         addy_type=Address.SHIPPING,
#         is_default=True,
#     ).first()


# def normalize_state(value: str) -> str:
#     state = (value or "").strip().upper()
#     if state == "OHIO":
#         return "OH"
#     return state


# def is_ohio_shipping(user) -> bool:
#     addy = get_default_shipping(user)
#     if not addy:
#         return False

#     country = (addy.country or "").strip().upper()
#     state = normalize_state(addy.state)
#     return country == "US" and state == "OH"


# def kyc_approved(user) -> bool:
#     return hasattr(user, "kyc") and user.kyc.status == KycProfile.APPROVED


# def has_proof_of_address(user) -> bool:
#     if not hasattr(user, "kyc"):
#         return False

#     return user.kyc.documents.filter(doc_type="proof_of_address").exists()


# def offer_eligible(user) -> bool:
#     return is_ohio_shipping(user) and kyc_approved(user)