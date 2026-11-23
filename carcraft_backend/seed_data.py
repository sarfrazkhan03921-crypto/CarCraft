"""
CarCraft Sample Data Seeder
Run with: python manage.py shell < seed_data.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carcraft_backend.settings')
django.setup()

from store.models import (
    CarMake, CarModel, Category, Brand, Product,
    WorkshopService, User, Coupon
)
from decimal import Decimal

print("=== Seeding CarCraft sample data ===")

# --- Car Makes ---
makes_data = [
    {'name': 'Hyundai', 'country': 'South Korea'},
    {'name': 'Tata', 'country': 'India'},
    {'name': 'Maruti Suzuki', 'country': 'India'},
    {'name': 'Honda', 'country': 'Japan'},
    {'name': 'Toyota', 'country': 'Japan'},
    {'name': 'Ford', 'country': 'USA'},
    {'name': 'BMW', 'country': 'Germany'},
]
for m in makes_data:
    CarMake.objects.get_or_create(name=m['name'], defaults={'country': m['country']})
print("[OK] Car makes seeded")

hyundai = CarMake.objects.get(name='Hyundai')
tata = CarMake.objects.get(name='Tata')
maruti = CarMake.objects.get(name='Maruti Suzuki')
honda = CarMake.objects.get(name='Honda')
toyota = CarMake.objects.get(name='Toyota')
bmw = CarMake.objects.get(name='BMW')

# --- Car Models ---
models_data = [
    {'make': hyundai, 'name': 'Creta', 'body_type': 'SUV', 'year_start': 2020},
    {'make': hyundai, 'name': 'Verna', 'body_type': 'Sedan', 'year_start': 2023},
    {'make': hyundai, 'name': 'i20', 'body_type': 'Hatchback', 'year_start': 2020},
    {'make': tata, 'name': 'Nexon', 'body_type': 'SUV', 'year_start': 2022},
    {'make': tata, 'name': 'Harrier', 'body_type': 'SUV', 'year_start': 2023},
    {'make': maruti, 'name': 'Swift', 'body_type': 'Hatchback', 'year_start': 2021},
    {'make': maruti, 'name': 'Baleno', 'body_type': 'Hatchback', 'year_start': 2022},
    {'make': honda, 'name': 'City', 'body_type': 'Sedan', 'year_start': 2020},
    {'make': toyota, 'name': 'Fortuner', 'body_type': 'SUV', 'year_start': 2021},
    {'make': bmw, 'name': '3 Series', 'body_type': 'Sedan', 'year_start': 2022},
]
for m in models_data:
    CarModel.objects.get_or_create(make=m['make'], name=m['name'], defaults={
        'body_type': m['body_type'], 'year_start': m['year_start']
    })
print("[OK] Car models seeded")

# --- Categories ---
cats_data = [
    {'name': 'Engine Parts', 'icon': 'Wrench'},
    {'name': 'Suspension & Brakes', 'icon': 'Gauge'},
    {'name': 'Exterior & Body', 'icon': 'Sparkles'},
    {'name': 'Interior & Comfort', 'icon': 'Flame'},
    {'name': 'Electrical & Lighting', 'icon': 'Zap'},
    {'name': 'Tyres & Wheels', 'icon': 'Circle'},
]
for c in cats_data:
    Category.objects.get_or_create(name=c['name'], defaults={'icon': c['icon'], 'is_active': True})
print("[OK] Categories seeded")

engine_cat = Category.objects.get(name='Engine Parts')
suspension_cat = Category.objects.get(name='Suspension & Brakes')
exterior_cat = Category.objects.get(name='Exterior & Body')
interior_cat = Category.objects.get(name='Interior & Comfort')
electrical_cat = Category.objects.get(name='Electrical & Lighting')
tyres_cat = Category.objects.get(name='Tyres & Wheels')

# --- Brands ---
brands_data = [
    'Bosch', 'Castrol', 'Monroe', 'Brembo', 'Philips', 'MRF', '3M', 'CarCraft OEM'
]
for b in brands_data:
    Brand.objects.get_or_create(name=b)
print("[OK] Brands seeded")

bosch = Brand.objects.get(name='Bosch')
castrol = Brand.objects.get(name='Castrol')
monroe = Brand.objects.get(name='Monroe')
brembo = Brand.objects.get(name='Brembo')
philips = Brand.objects.get(name='Philips')
mrf = Brand.objects.get(name='MRF')
three_m = Brand.objects.get(name='3M')
oem = Brand.objects.get(name='CarCraft OEM')

# --- Products ---
prods = [
    {
        'sku': 'CC-ENG-001', 'name': 'Castrol Edge 5W-30 Engine Oil (1L)',
        'category': engine_cat, 'brand': castrol,
        'price': Decimal('899'), 'discount_price': Decimal('749'),
        'stock': 50, 'is_featured': True, 'is_bestseller': True,
        'short_description': 'Full synthetic engine oil for peak performance',
        'description': 'Castrol EDGE 5W-30 full synthetic engine oil. Advanced Fluid Titanium Technology. Suitable for petrol and diesel engines. Reduces engine wear even under extreme pressure.',
        'main_image': '',
    },
    {
        'sku': 'CC-ENG-002', 'name': 'Bosch Oil Filter',
        'category': engine_cat, 'brand': bosch,
        'price': Decimal('350'), 'discount_price': Decimal('299'),
        'stock': 80, 'is_featured': False, 'is_bestseller': True,
        'short_description': 'High-performance oil filter for all engines',
        'description': 'Bosch premium oil filter for maximum engine protection. Removes particles and contaminants. Long-life filter media ensures consistent performance. Compatible with most petrol and diesel engines.',
        'main_image': '',
    },
    {
        'sku': 'CC-AIR-001', 'name': 'Bosch Air Filter',
        'category': engine_cat, 'brand': bosch,
        'price': Decimal('450'), 'discount_price': None,
        'stock': 60, 'is_featured': False, 'is_bestseller': False,
        'short_description': 'Premium air filter for better engine breathing',
        'description': 'Bosch air filter ensures clean air supply to your engine. Prevents dust and debris from entering the engine. Improves fuel efficiency and engine performance.',
        'main_image': '',
    },
    {
        'sku': 'CC-SUS-001', 'name': 'Monroe Shock Absorber (Front)',
        'category': suspension_cat, 'brand': monroe,
        'price': Decimal('2499'), 'discount_price': Decimal('1999'),
        'stock': 20, 'is_featured': True, 'is_bestseller': False,
        'short_description': 'Front shock absorber for smooth ride quality',
        'description': 'Monroe OESpectrum front shock absorber. Original equipment quality for perfect fit and performance. Maintains road contact and vehicle stability. Sold as single unit.',
        'main_image': '',
    },
    {
        'sku': 'CC-BRK-001', 'name': 'Brembo Brake Pads (Front Set)',
        'category': suspension_cat, 'brand': brembo,
        'price': Decimal('1899'), 'discount_price': Decimal('1599'),
        'stock': 30, 'is_featured': True, 'is_bestseller': True,
        'short_description': 'Premium front brake pads for reliable stopping',
        'description': 'Brembo OEM brake pads set for front axle. Superior braking performance and durability. Low noise and dust. Includes shims and hardware for easy installation.',
        'main_image': '',
    },
    {
        'sku': 'CC-INT-001', 'name': '3D Luxury Seat Cover Set',
        'category': interior_cat, 'brand': three_m,
        'price': Decimal('4999'), 'discount_price': Decimal('3799'),
        'stock': 25, 'is_featured': True, 'is_bestseller': False,
        'short_description': 'Full car seat cover set — waterproof & breathable',
        'description': '3D luxury car seat cover set. Waterproof and breathable neoprene fabric. Easy to install and remove. Fits most hatchbacks and sedans. Includes front and rear covers.',
        'main_image': '',
    },
    {
        'sku': 'CC-INT-002', 'name': 'Car Floor Mat Set (7D)',
        'category': interior_cat, 'brand': oem,
        'price': Decimal('1799'), 'discount_price': Decimal('1399'),
        'stock': 40, 'is_featured': False, 'is_bestseller': True,
        'short_description': '7D rubber floor mats — heavy duty anti-slip',
        'description': 'Premium 7D car floor mats. Heavy-duty rubber with anti-slip bottom. Custom-fit design for most Indian cars. Easy to clean and maintain. Includes driver, passenger, and rear mats.',
        'main_image': '',
    },
    {
        'sku': 'CC-EXT-001', 'name': 'Roof Spoiler (Universal)',
        'category': exterior_cat, 'brand': oem,
        'price': Decimal('3500'), 'discount_price': Decimal('2899'),
        'stock': 15, 'is_featured': False, 'is_bestseller': False,
        'short_description': 'Universal rear roof spoiler for sporty look',
        'description': 'Universal fit rear roof spoiler in ABS plastic. Aerodynamic design reduces drag. Self-adhesive and screw mount installation. Can be painted to match your car color.',
        'main_image': '',
    },
    {
        'sku': 'CC-ELC-001', 'name': 'Philips X-treme Vision H4 Bulb (2 pcs)',
        'category': electrical_cat, 'brand': philips,
        'price': Decimal('699'), 'discount_price': Decimal('549'),
        'stock': 100, 'is_featured': False, 'is_bestseller': True,
        'short_description': 'High-performance H4 halogen headlight bulbs',
        'description': 'Philips X-treme Vision Plus H4 halogen bulbs. Up to 130% more light on road vs standard bulbs. Longer lifespan. Improved visibility in rain and fog. Pack of 2.',
        'main_image': '',
    },
    {
        'sku': 'CC-TYR-001', 'name': 'MRF ZLX 185/65 R15 Tyre',
        'category': tyres_cat, 'brand': mrf,
        'price': Decimal('4200'), 'discount_price': None,
        'stock': 12, 'is_featured': True, 'is_bestseller': False,
        'short_description': 'MRF ZLX all-season tyre for hatchbacks and sedans',
        'description': 'MRF ZLX 185/65 R15 tubeless radial tyre. Excellent wet and dry grip. Low rolling resistance for better fuel economy. Suitable for Maruti Swift, Hyundai i20, and similar cars.',
        'main_image': '',
    },
]

for p in prods:
    obj, created = Product.objects.get_or_create(sku=p['sku'], defaults={
        'name': p['name'],
        'category': p['category'],
        'brand': p['brand'],
        'price': p['price'],
        'discount_price': p['discount_price'],
        'stock': p['stock'],
        'in_stock': True,
        'is_featured': p['is_featured'],
        'is_bestseller': p['is_bestseller'],
        'short_description': p['short_description'],
        'description': p['description'],
        'main_image': p['main_image'],
    })
    if created:
        print(f"  Created: {obj.name}")

print("[OK] Products seeded")

# --- Workshop Services ---
services = [
    {
        'name': 'Engine Service & Tune-up',
        'short_description': 'Complete engine health check and tune-up service',
        'description': 'Full engine diagnostic scan, spark plug replacement, air filter, fuel filter, throttle body cleaning, and performance optimization.',
        'base_price': Decimal('1999'),
        'estimated_duration_hours': Decimal('3.0'),
        'is_active': True, 'is_popular': True,
    },
    {
        'name': 'Full Service (5000 km)',
        'short_description': 'Complete 5000km service with oil change and checks',
        'description': 'Engine oil and filter change, brake inspection, tyre rotation, fluid level checks, battery health check, AC filter cleaning.',
        'base_price': Decimal('2499'),
        'estimated_duration_hours': Decimal('4.0'),
        'is_active': True, 'is_popular': True,
    },
    {
        'name': 'Tyre & Wheel Alignment',
        'short_description': 'Computerized wheel alignment and tyre rotation',
        'description': 'Full 4-wheel computerized alignment, tyre balancing, and rotation. Improves tyre life and fuel efficiency.',
        'base_price': Decimal('799'),
        'estimated_duration_hours': Decimal('1.5'),
        'is_active': True, 'is_popular': False,
    },
    {
        'name': 'Brake Inspection & Service',
        'short_description': 'Complete brake system inspection and servicing',
        'description': 'Brake pad measurement, disc/drum inspection, brake fluid flush, caliper lubrication, and test drive verification.',
        'base_price': Decimal('1299'),
        'estimated_duration_hours': Decimal('2.0'),
        'is_active': True, 'is_popular': False,
    },
    {
        'name': 'AC Service & Gas Refill',
        'short_description': 'Car air conditioning service and refrigerant top-up',
        'description': 'AC gas (R134a) leak test and recharge, cabin air filter replacement, compressor belt check, vent cleaning.',
        'base_price': Decimal('1499'),
        'estimated_duration_hours': Decimal('2.5'),
        'is_active': True, 'is_popular': True,
    },
    {
        'name': 'Car Wash & Detailing',
        'short_description': 'Professional exterior wash and interior detailing',
        'description': 'Full exterior wash, wax polish, interior vacuuming, dashboard cleaning, glass treatment, and tyre dressing.',
        'base_price': Decimal('599'),
        'estimated_duration_hours': Decimal('1.5'),
        'is_active': True, 'is_popular': False,
    },
]

from django.utils.text import slugify

for s in services:
    s_slug = slugify(s['name'])
    WorkshopService.objects.get_or_create(slug=s_slug, defaults={
        'name': s['name'],
        'short_description': s['short_description'],
        'description': s['description'],
        'base_price': s['base_price'],
        'estimated_duration_hours': s['estimated_duration_hours'],
        'is_active': s['is_active'],
        'is_popular': s['is_popular'],
    })
print("[OK] Workshop services seeded")

# --- Coupons ---
from django.utils import timezone
Coupon.objects.get_or_create(code='CARCRAFT10', defaults={
    'discount_type': 'percent',
    'discount_value': Decimal('10'),
    'max_discount': Decimal('500'),
    'min_order_amount': Decimal('0'),
    'usage_limit': 1000,
    'is_active': True,
})
Coupon.objects.get_or_create(code='WELCOME50', defaults={
    'discount_type': 'fixed',
    'discount_value': Decimal('50'),
    'min_order_amount': Decimal('500'),
    'usage_limit': 500,
    'is_active': True,
})
print("[OK] Coupons seeded")

print("")
print("=== Seeding complete! ===")
print(f"  CarMakes: {CarMake.objects.count()}")
print(f"  CarModels: {CarModel.objects.count()}")
print(f"  Categories: {Category.objects.count()}")
print(f"  Brands: {Brand.objects.count()}")
print(f"  Products: {Product.objects.count()}")
print(f"  Services: {WorkshopService.objects.count()}")
print(f"  Coupons: {Coupon.objects.count()}")
