from django.contrib import admin
from . import models

@admin.register(models.Book)
class BookAdmin(admin.ModelAdmin):
    def number_of_instances(self):
        return self.bookinstance_set.count()
    number_of_instances.short_description = "Количество экземпляров"
    
        
    search_fields = ['name', 'authors', 'subject',
                     'grade', 'isbn', 'inventory_number']
    
    list_display=(
        'authors', 
        'name',
        'isbn',
        'inventory_number',
        number_of_instances,
    )
    
    fieldsets = (
      ("Идентификаторы", {'fields':
        ('isbn', 'inventory_number')
      }),
      
      ('Основная информация', {'fields':
        ('name', 'authors')
      }),
      
      ('Информация об издании', {'fields':
        ('publisher', 'city',
         'year', 'edition')
      }),
      
      ("Учебная информация", {'fields':
        ('grade', 'subject')
      }),
    )

@admin.register(models.BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'book', 'status')
    readonly_fields = ('status',)
    fields = ('status', 'barcode', 'book', "notes")
    autocomplete_fields = ['book']
    search_fields = ('barcode', 'book__name', 'book__authors')