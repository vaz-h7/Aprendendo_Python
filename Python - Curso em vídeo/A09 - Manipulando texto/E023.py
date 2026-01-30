numero = int(input('Informe um número: '))
'''
num = str(numero)
print(f'Analisando o número {num}...')
print(f'Unidade: {num[3]}')
print(f'Dezena: {num[2]}')
print(f'Centena: {num[1]}')
print(f'Milhar: {num[0]}')
'''
u = numero // 1 % 10
d = numero // 10 % 10
c = numero // 100 % 10
m = numero // 1000 % 10
print(f'Analisando o número {numero}...')
print(f'Unidade: {u}\nDezena: {d}\nCentena: {c}\nMilhar: {m}')
#Repare que aqui estamos trabalhando com número inteiros. Se não fossem inteiros, o programa ia reponder de outra forma.
