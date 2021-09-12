from decimal import Decimal
import decimal
from copy import deepcopy

class Transfer:
    def __init__(self):
        self.json = {}
    
    def name_io(self):
        name = input("Введите название счёта, по которому произошёл трансфер денег. В качестве разделителя используйте точку. Пример: «Активы.Наличные.Чёрный кошелёк.₽»\n")
        path = name.split(".")
        target = self.json
        for point in path:
            target[point] = {}
            target = target[point]
        return target

    @staticmethod
    def concat_dicts(dict1: dict, dict2: dict) -> dict:
        output = {}
        for k in set(dict1.keys()) | set(dict2.keys()):
            if k in dict1 and k in dict2:
                output[k] = Transfer.concat_dicts(dict1[k], dict2[k])
            elif k in dict1:
                output[k] = deepcopy(dict1[k])
            else: # elif k in dict2:
                output[k] = deepcopy(dict2[k])
        return output

    @classmethod
    def io(cls):
        output = Transfer()
        target = output.name_io()
        kind = None
        while True:
            try:
                kind = input("1. «difference». Тип трансфера является разницей (чаще всего).\n2. «set». Тип трансфера является отожествление значения счёта. Значение денег установится тем числом, которое вы введёте.\nВведите «1» или «2».\n")
                kind = int(kind)
                break
            except Exception as e:
                print(f"Не получилось определить тип счёта. Вы ввели «{kind}». Требовалось число 1 или 2.\n")
        # try:
		# 	self._actual_sum = Decimal(actual_sum)
		# except decimal.InvalidOperation as e:
		# 	raise ValueError(f"Не получилось прочитать цену позиции в чеке. Пример правильного числа: «{Decimal('25.12')}»") from e
        

    def __dict__(self):
        return self.json
