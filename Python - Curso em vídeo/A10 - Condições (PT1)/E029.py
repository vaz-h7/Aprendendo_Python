vel_atual = int(input('Qual a velocidade atual do carro? '))
limite = 80
if vel_atual > limite:
    print(f'MULTADO! Você excedeu o limite permitido que é de 80Km/h')
    multa = (vel_atual-80) * 7
    print(f'Você deve pagar uma multa de R${multa:.2f}!')
print('Tenha um bom dia! Dirija com segurança!')
