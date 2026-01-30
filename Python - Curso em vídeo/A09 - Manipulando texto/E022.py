nome = str(input('Digite seu nome: ')).strip() #Comando strip para retirar os espaços antes e depois da str.
print('Analisando seu nome...')
print(f'Seu nome em maiúsculas é {nome.upper()}')
print(f'Seu nome em minúsculas é {nome.lower()}')
print(f'Seu nome tem ao todo {len(nome) - nome.count(' ')} letras') #Len faz a contagem das str's e usamos o '-nome.count(' ')' para retirar os espaços entre a str.
nome_separado = (nome.split())
print(f'Seu primeiro nome é {nome_separado[0]} e tem {len(nome_separado[0])} letras')
