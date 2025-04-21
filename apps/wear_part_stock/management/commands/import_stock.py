import math
import unicodedata
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from apps.wear_part_stock.models import WearPartStock
from apps.equipment_management.models import Manufacturer

def clean_text(x):
    if pd.isna(x):
        return ""
    s = str(x).strip().upper()
    return unicodedata.normalize('NFKD', s).encode('ASCII','ignore').decode()

def strip_text(x):
    if pd.isna(x):
        return ""
    return str(x).strip()

class Command(BaseCommand):
    help = 'Import wear part stock data from Excel (group duplicates by part_no)'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str)

    def handle(self, *args, **opts):
        df = pd.read_excel(opts['excel_file'])
        expected = ['manufacturer', 'name', 'stock_quantity','min_threshold', 'unit', 'manufacturer_id', 'alternative_id']
        missing = [c for c in expected if c not in df.columns]
        if missing:
            raise CommandError(f"Missing columns: {missing}")

        # Sử dụng clean_text cho các trường cần chuẩn hóa
        df['manufacturer'] = df['manufacturer'].apply(clean_text)
        df['manufacturer_id'] = df['manufacturer_id'].apply(clean_text)
        df['alternative_id'] = df['alternative_id'].apply(clean_text)

        # Giữ nguyên tiếng Việt cho các trường name và unit (chỉ loại bỏ khoảng trắng)
        df['name'] = df['name'].apply(strip_text)
        df['unit'] = df['unit'].apply(strip_text)

        # Gom nhóm theo manufacturer_id (đã chuẩn hóa)
        grouped = df.groupby('manufacturer_id', as_index=False).agg({
            'manufacturer': 'first',
            'name': 'first',
            'unit': 'first',
            'alternative_id': 'first',
            'stock_quantity': 'sum',
            'min_threshold': 'first'
        })

        total = 0
        for row in grouped.to_dict('records'):
            manu_name = row['manufacturer'] or "SHARED"
            manu_obj, _ = Manufacturer.objects.get_or_create(name=manu_name)

            part_no = row['manufacturer_id']
            qty = int(row['stock_quantity'])
            alt = row['alternative_id'] or None
            threshold = int(row.get('min_threshold'))
            obj, created = WearPartStock.objects.update_or_create(
                manufacturer_id=part_no,
                defaults={
                    'name': row['name'],
                    'stock_quantity': qty,
                    'unit': row['unit'],
                    'alternative_id': alt,
                    'min_threshold': threshold,
                }
            )


            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} {part_no} → qty={qty}")
            total += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {total} unique parts"))
