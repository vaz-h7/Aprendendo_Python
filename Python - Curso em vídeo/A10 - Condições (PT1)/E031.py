distância = float(input('Qual a distância em Km da sua viagem? '))
print(f'Você está prestes a começar uma viagem de {distância}Km.')
'''
if distância <= 200:
    print(f'O valor da sua viagem vai custar R${distância * 0.50}!')
else:
    print(f'O valor da sua viagem vai custar R${distância * 0.45}!')
'''
if distância <= 200:
    preço = distância * 0.50
else:
    preço = distância * 0.45
print(f'Você pagará R${preço:.2f} na sua passagem!')