import unicodedata #Esta biblioteca será usada em dois comandos para remover as acentuações.
frase = str(input('Digite uma frase: ')).strip().lower()
nfd_form = unicodedata.normalize('NFD', frase)
frase = "".join(c for c in nfd_form if unicodedata.category(c) != 'Mn')
print(f'A letra "A" aparece {frase.count("a")} vezes na frase.')
print(f'A primeira letra "A" aparece na posição {frase.find("a")+1}')
print(f'A última letra "A" aparece na posição {frase.rfind("a")+1}')
