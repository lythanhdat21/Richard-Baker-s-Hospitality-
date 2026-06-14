from decimal import Decimal

from src.app.mappers import folio_mapper, guest_mapper, reservation_mapper, room_mapper
from src.app.schemas.internal.reservation import ReservationSearchRequest


def test_to_opera_search_params_confirmation():
    req = ReservationSearchRequest(confirmation_number="ABC123")
    params = reservation_mapper.to_opera_search_params(req)
    assert params.confirmation_number == "ABC123"


def test_to_opera_search_params_guest_name_split():
    req = ReservationSearchRequest(guest_name="Nguyen Van A")
    params = reservation_mapper.to_opera_search_params(req)
    assert params.given_name == "Nguyen"
    assert params.surname == "Van A"


def test_to_internal_summary():
    opera_res = {
        "reservationIdList": [
            {"id": "RES001", "type": "Reservation"},
            {"id": "CONF001", "type": "Confirmation"},
        ],
        "reservationStatus": "RESERVED",
        "roomStay": {
            "expectedTimes": {
                "reservationExpectedArrivalTime": "2026-06-10T14:00:00Z",
                "reservationExpectedDepartureTime": "2026-06-12T12:00:00Z",
            },
            "currentRoomInfo": {"roomId": "1208"},
        },
    }
    summary = reservation_mapper.to_internal_summary(opera_res)
    assert summary.reservation_id == "RES001"
    assert summary.confirmation_number == "CONF001"
    assert summary.status == "RESERVED"
    assert summary.arrival_date == "2026-06-10"
    assert summary.room_number == "1208"


def test_to_internal_room_status():
    opera_room = {
        "room": {
            "roomId": "1208",
            "occupancyStatus": "OCCUPIED",
            "housekeeping": {"status": "CLEAN"},
            "roomType": "DLX",
            "floor": "12",
        }
    }
    status = room_mapper.to_internal_room_status(opera_room)
    assert status.room_number == "1208"
    assert status.occupancy_status == "OCCUPIED"
    assert status.housekeeping_status == "CLEAN"
    assert status.floor == "12"


def test_to_internal_guest():
    opera_profile = {
        "profileId": {"id": "P001"},
        "customer": {
            "personName": [{"givenName": "Nguyen", "surname": "Van A"}],
            "nationality": "VN",
        },
        "eMails": [{"emailAddress": "test@example.com"}],
        "telephones": [{"phoneNumber": "0901234567"}],
    }
    guest = guest_mapper.to_internal_guest(opera_profile)
    assert guest.profile_id == "P001"
    assert guest.first_name == "Nguyen"
    assert guest.last_name == "Van A"
    assert guest.email == "test@example.com"
    assert guest.nationality == "VN"


def test_to_internal_folio_summary_filters_sensitive_payment_data():
    opera_folio = {
        "reservationFolioInformation": {
            "postStayChargeAllowed": True,
            "roomAndTaxPosted": False,
            "folioWindows": [
                {
                    "folioWindowNo": 1,
                    "balance": {"amount": "120.50", "currencyCode": "USD"},
                    "revenue": {"amount": "200.50", "currencyCode": "USD"},
                    "payment": {"amount": "80.00", "currencyCode": "USD"},
                    "paymentMethod": {"cardNumber": "4111111111111111"},
                    "folios": [{"folioNo": 10}, {"folioNo": 11}],
                    "confidential": True,
                }
            ],
        }
    }

    folio = folio_mapper.to_internal_folio_summary(opera_folio, "RES001")

    assert folio.reservation_id == "RES001"
    assert folio.windows[0].window_no == 1
    assert folio.windows[0].balance.amount == Decimal("120.50")
    assert folio.windows[0].balance.currency_code == "USD"
    assert folio.windows[0].folio_count == 2
    assert not hasattr(folio.windows[0], "paymentMethod")


def test_to_internal_payment_status_marks_zero_balance_as_paid():
    status = folio_mapper.to_internal_payment_status(
        {"paymentBalance": {"amount": "0.00", "currencyCode": "USD"}},
        "RES001",
    )

    assert status.reservation_id == "RES001"
    assert status.balance.amount == Decimal("0.00")
    assert status.is_paid is True
