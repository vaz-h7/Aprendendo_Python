salário = float(input('Qual o salário do funcionário? R$'))
if salário <= 1250.00:
    novo = salário * 1.15
else:
    novo = salário * 1.10
print(f'Quem ganhava R${salário:.2f} passa a ganhar R${novo:.2f} agora!')
