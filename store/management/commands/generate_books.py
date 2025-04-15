# store/management/commands/generate_books.py

from django.core.management.base import BaseCommand
from faker import Faker
from store.models import Book, Author, Genre, Publisher, Category
import random
import os

fake = Faker('ru_RU')

BOOK_IMAGES = [
    'books/sample1.jpg',
    'books/sample2.jpg',
    'books/sample3.jpg',
    'books/sample4.jpg',
    'books/sample5.jpg',
]

class Command(BaseCommand):
    help = 'Генерирует фейковые книги по жанрам'

    def handle(self, *args, **kwargs):
        genres = Genre.objects.select_related('category').all()
        publishers = ['Издательство АСТ', 'Эксмо', 'Манн, Иванов и Фербер']
        
        for pub_name in publishers:
            Publisher.objects.get_or_create(name=pub_name)

        created_count = 0

        for genre in genres:
            for _ in range(1):  # по одной книге на каждый жанр
                author = Author.objects.create(name=fake.name())
                publisher = Publisher.objects.order_by('?').first()
                title = fake.sentence(nb_words=4)
                description = fake.text(max_nb_chars=500)
                year = random.randint(1980, 2024)
                price = round(random.uniform(300, 2000), 2)
                image = random.choice(BOOK_IMAGES)

                Book.objects.create(
                    title=title,
                    author=author,
                    genre=genre,
                    publisher=publisher,
                    description=description,
                    year=year,
                    price=price,
                    image=image,
                    discount=random.choice([0, 5, 10, 15]),
                    cashback=random.choice([0, 20, 50]),
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Сгенерировано {created_count} книг'))
