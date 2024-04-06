from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files import File
from datetime import timedelta, date, datetime
import csv
from ...models import User, UserProfile, Product, Inventory, Discount, Category, ProductImage, Order, OrderDetails


class Command(BaseCommand):
    help = 'Imports data from Testing.csv'

    def handle(self, *args, **options):
        # Create the vendor user if it doesn't exist
        vendor_user, created = User.objects.get_or_create(
            username='nishant',
            defaults={
                'email': 'nishant@example.com',
                'first_name': 'Nishant',
                'last_name': 'Vendor',
                'phone_number': '1234567890',
                'address': 'Vendor City, Vendor State, Vendor Country',
                'date_joined': timezone.now() - timedelta(days=1500)
            }
        )
        if created:
            vendor_user.set_password('nishant')
            vendor_user.save()

        UserProfile.objects.get_or_create(
            user=vendor_user,
            defaults={
                'is_vendor': True,
                'gender': 'M',
                'date_of_birth': '1990-01-01'
            }
        )

        with open('Testing.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Create or retrieve the user
                norm_user, created = User.objects.get_or_create(
                    username=row['Customer ID'],
                    defaults={
                        'email': f"{row['Customer ID']}@example.com",
                        'first_name': row['Customer Name'].split()[0],
                        'last_name': row['Customer Name'].split()[1] if len(row['Customer Name'].split()) > 1 else '',
                        'phone_number': '1234567890',
                        'address': f"{row['City']}, {row['State']}, {row['Country']}",
                        'date_joined': timezone.now() - timedelta(days=1500),
                    }
                )

                if created:
                    norm_user.set_password('password')
                    norm_user.save()
                    print(f"User {norm_user.username} created.")

                age = int(float(row['corrected_age']))
                date_of_birth = date(date.today().year - age, 1, 1)

                user_profile, _ = UserProfile.objects.get_or_create(
                    user=norm_user,
                    defaults={
                        'is_vendor': False,
                        'gender': row['corrected_gender'][0],
                        'date_of_birth': date_of_birth
                    }
                )
                print(f"User {norm_user.username} test.")

                # Create or retrieve the category
                category, _ = Category.objects.get_or_create(
                    name=row['Sub-Category'],
                    defaults={
                        'description': f"This is the {row['Sub-Category']} category."
                    }
                )

                # Create the Inventory instance
                inventory_defaults = {
                    'current_stock': int(float(row['corrected_stock'])),
                    'safety_stock_level': int(float(row['corrected_stock']) * 0.2),
                    'reorder_point': int(float(row['corrected_stock']) * 0.1),
                }
                inventory, _ = Inventory.objects.get_or_create(
                    **inventory_defaults)

                # Create the Discount instance
                discount_defaults = {
                    'discount_type': Discount.DiscountType.FIXED,
                    'discount_value': 10,
                    'start_date': timezone.now(),
                    'end_date': timezone.now() + timedelta(days=1),
                }
                discount, _ = Discount.objects.get_or_create(
                    **discount_defaults)

                additional_views = int(float(row['Quantity']))

                # Now include both 'inventory' and 'discount' in the defaults for Product creation
                product, created = Product.objects.get_or_create(
                    name=row['Product Name'],
                    defaults={
                        'description': f"This is the description for {row['Product Name']} of {row['Sub-Category']} category.",
                        'price': float(row['Average Price']),
                        'user': vendor_user,
                        'inventory': inventory,  # Associate Inventory here
                        'discount': discount,  # Associate Discount here
                        'total_views': additional_views,
                    }
                )

                if not created:
                    product.total_views += additional_views
                    product.save()

                # Add the category to the product
                product.categories.add(category)

                # Create the product image if it doesn't exist
                if not ProductImage.objects.filter(product=product).exists():
                    with open('test.png', 'rb') as image_file:
                        ProductImage.objects.create(
                            image=File(image_file, name='test.png'),
                            description='test',
                            upload_date=timezone.now(),
                            product=product
                        )

                # Create the order and order details
                order_date = datetime.strptime(row['Order Date'], '%Y-%m-%d')
                order = Order.objects.create(
                    order_date=order_date,
                    total_amount=float(row['Sales']),
                    status='Completed',
                    user=norm_user
                )
                OrderDetails.objects.create(
                    quantity=int(float(row['Quantity'])),
                    price=float(row['Average Price']),
                    order=order,
                    product=product
                )

        self.stdout.write(self.style.SUCCESS('Data imported successfully.'))
