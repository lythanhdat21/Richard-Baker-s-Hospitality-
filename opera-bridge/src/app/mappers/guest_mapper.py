from src.app.schemas.internal.guest import GuestProfile


def to_internal_guest(opera_profile: dict) -> GuestProfile:
    profile_id = opera_profile.get("profileId", {}).get("id") or opera_profile.get("profileId") or ""
    customer = opera_profile.get("customer", {})
    person_names = customer.get("personName", [{}])
    first_name = person_names[0].get("givenName") if person_names else None
    last_name = person_names[0].get("surname") if person_names else None

    emails = opera_profile.get("eMails", [])
    email = emails[0].get("emailAddress") if emails else None

    phones = opera_profile.get("telephones", [])
    phone = phones[0].get("phoneNumber") if phones else None

    nationality = customer.get("nationality")

    return GuestProfile(
        profile_id=str(profile_id),
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        nationality=nationality,
    )
