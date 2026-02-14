número = int(input('Me diga um número qualquer: '))
resultado = número % 2 #O resto da divisão por 2 de qualquer número PAR é 0 e de qualquer número ÍMPAR é 1
print(f'O número escolhido foi {número}!')
if resultado == 1:
    print(f'O número {número} é ÍMPAR!')
else:
    print(f'O número {número} é PAR!')
