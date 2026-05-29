from datetime import datetime, timezone as dt_timezone

from django.test import TestCase

from moons.models import InvoiceRecord, MiningObservation, MoonRental


class TestMiningObservationBuildPk(TestCase):
    def test_format(self):
        dt = datetime(2024, 3, 15, tzinfo=dt_timezone.utc)
        pk = MiningObservation.build_pk(
            corp_id=123,
            observer_id=456,
            observed_character_id=789,
            ob_date=dt,
            type_id=46295,
        )
        self.assertEqual(pk, "123-456-789-20240315-46295")

    def test_date_zero_pads_month_and_day(self):
        dt = datetime(2024, 1, 5, tzinfo=dt_timezone.utc)
        pk = MiningObservation.build_pk(1, 2, 3, dt, 100)
        self.assertIn("20240105", pk)


class TestInvoiceRecordSanitizeDate(TestCase):
    def test_zeroes_time_components(self):
        dt = datetime(2024, 6, 15, 14, 30, 45, tzinfo=dt_timezone.utc)
        result = InvoiceRecord.sanitize_date(dt)
        self.assertEqual(result.hour, 0)
        self.assertEqual(result.minute, 0)
        self.assertEqual(result.second, 0)

    def test_preserves_date_and_timezone(self):
        dt = datetime(2024, 6, 15, 14, 30, tzinfo=dt_timezone.utc)
        result = InvoiceRecord.sanitize_date(dt)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 6)
        self.assertEqual(result.day, 15)
        self.assertEqual(result.tzinfo, dt.tzinfo)


class TestInvoiceRecordGetLastDate(TestCase):
    def test_no_records_returns_datetime_min(self):
        self.assertEqual(InvoiceRecord.get_last_invoice_date(), datetime.min)

    def test_returns_most_recent_end_date(self):
        InvoiceRecord.objects.create(
            start_date=datetime(2024, 1, 1, tzinfo=dt_timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=dt_timezone.utc),
            ore_prices="{}", tax_dump="{}", total_mined=0, total_taxed=0,
        )
        newer = InvoiceRecord.objects.create(
            start_date=datetime(2024, 2, 1, tzinfo=dt_timezone.utc),
            end_date=datetime(2024, 2, 29, tzinfo=dt_timezone.utc),
            ore_prices="{}", tax_dump="{}", total_mined=0, total_taxed=0,
        )
        self.assertEqual(InvoiceRecord.get_last_invoice_date(), newer.end_date)


class TestInvoiceRecordGenerateInvRef(TestCase):
    def test_format(self):
        start = datetime(2024, 1, 1, tzinfo=dt_timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=dt_timezone.utc)
        ref = InvoiceRecord.generate_inv_ref(42, start, end)
        self.assertEqual(ref, "MT42-20240101-20240131")


class TestMoonRentalGenerateInvRef(TestCase):
    def test_monthly_format(self):
        inv_date = datetime(2024, 3, 15, tzinfo=dt_timezone.utc)
        ref = MoonRental.generate_inv_ref(99, inv_date)
        self.assertEqual(ref, "MR99-202403")

    def test_single_appends_hash_suffix(self):
        inv_date = datetime(2024, 3, 15, 10, 30, tzinfo=dt_timezone.utc)
        ref = MoonRental.generate_inv_ref(99, inv_date, single="abc12345")
        self.assertEqual(ref, "MR99-20240315-1030-abc12345")
