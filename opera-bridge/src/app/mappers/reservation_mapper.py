from src.app.schemas.internal.reservation import ReservationSearchRequest, ReservationSummary, ReservationDetail
from src.app.schemas.opera.reservation import OperaReservationSearchParams


def to_opera_search_params(req: ReservationSearchRequest) -> OperaReservationSearchParams:
    parts = (req.guest_name or "").split(" ", 1)
    given_name = parts[0] if parts else None
    surname = parts[1] if len(parts) > 1 else None

    return OperaReservationSearchParams(
        confirmation_number=req.confirmation_number,
        given_name=given_name,
        surname=surname,
        arrival_date_start=req.arrival_date,
        arrival_date_end=req.arrival_date,
    )


def _guest_name(opera_res: dict) -> str | None:
    try:
        profiles = opera_res.get("reservationGuests", [])
        if profiles:
            name = profiles[0].get("profileInfo", {}).get("profile", {}).get("customer", {})
            first = name.get("personName", [{}])[0].get("givenName", "")
            last = name.get("personName", [{}])[0].get("surname", "")
            return f"{first} {last}".strip() or None
    except (KeyError, IndexError, TypeError):
        return None
    return None


def to_internal_summary(opera_res: dict) -> ReservationSummary:
    res_id_list = opera_res.get("reservationIdList", [])
    res_id = next((r.get("id") for r in res_id_list if r.get("type") == "Reservation"), None)
    conf_num = next((r.get("id") for r in res_id_list if r.get("type") == "Confirmation"), None)

    room_info = opera_res.get("roomStay", {})
    room_number = room_info.get("currentRoomInfo", {}).get("roomId")
    arrival = room_info.get("expectedTimes", {}).get("reservationExpectedArrivalTime")
    departure = room_info.get("expectedTimes", {}).get("reservationExpectedDepartureTime")
    if arrival:
        arrival = arrival[:10]
    if departure:
        departure = departure[:10]

    return ReservationSummary(
        reservation_id=res_id or "",
        confirmation_number=conf_num,
        guest_name=_guest_name(opera_res),
        arrival_date=arrival,
        departure_date=departure,
        status=opera_res.get("reservationStatus"),
        room_number=room_number,
    )


def to_internal_detail(opera_res: dict) -> ReservationDetail:
    summary = to_internal_summary(opera_res)
    room_stay = opera_res.get("roomStay", {})
    rate_plan = room_stay.get("ratePlans", [{}])[0].get("ratePlanCode") if room_stay.get("ratePlans") else None
    room_type = room_stay.get("roomTypes", [{}])[0].get("roomTypeCode") if room_stay.get("roomTypes") else None
    adults = room_stay.get("guestCounts", {}).get("adultCount")
    children = room_stay.get("guestCounts", {}).get("childCount")

    return ReservationDetail(
        **summary.model_dump(),
        hotel_id=opera_res.get("hotelId"),
        adults=adults,
        children=children,
        room_type=room_type,
        rate_plan=rate_plan,
    )
