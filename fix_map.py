import csv
import os

def fix_map(filename):
    if not os.path.exists(filename) and os.path.exists(os.path.join('levels', filename)):
        filename = os.path.join('levels', filename)
    with open(filename, newline='') as f:
        reader = csv.reader(f, delimiter=',')
        data = [list(row) for row in reader]
    
    # Encontrar as caixas de vida (tile 19)
    for y in range(len(data)):
        for x in range(len(data[y])):
            if data[y][x] == '19' and y < 8:  # Foca nas plataformas altas
                # Achou a caixa de vida em (y, x). 
                # Vamos identificar os limites da plataforma na linha de baixo (y + 1)
                plat_y = y + 1
                
                # Mover caixa de vida e decoração (se houver) ao redor 1 linha para baixo
                # Bem como a plataforma
                
                left_edge = x
                while left_edge > 0 and data[plat_y][left_edge - 1] in ['6', '7', '8', '0', '1', '2']:
                    left_edge -= 1
                    
                right_edge = x
                while right_edge < len(data[plat_y]) - 1 and data[plat_y][right_edge + 1] in ['6', '7', '8', '0', '1', '2']:
                    right_edge += 1
                
                # Deslocar para baixo
                for col in range(left_edge, right_edge + 1):
                    # Move o bloco de terra para baixo
                    data[plat_y + 1][col] = data[plat_y][col]
                    data[plat_y][col] = '-1'
                    
                    # Move o que estiver em cima da terra (ex: caixa de vida, decoração) para baixo
                    if data[y][col] != '-1':
                        data[y + 1][col] = data[y][col]
                        data[y][col] = '-1'

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        for row in data:
            writer.writerow(row)
            
    print(f"Mapa {filename} corrigido com sucesso!")

if __name__ == '__main__':
    fix_map('level1_data.csv')
