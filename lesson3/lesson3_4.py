import random

while(True):
    min = 1
    max = 100
    count = 0
    target = random.randint(min,max)
    print(target)
    print("============猜數字遊戲===========\n")
    while(True):
        keyin = int(input(f"猜數字範圍{min}~{max}:"))
        count += 1
        if keyin >= min and keyin <=max:
            if target == keyin:
                print(f"賓果!猜對了, 答案是:{target}")
                print(f"您猜了{count}")
                break
            elif (keyin > target):
                print("再小一點")
                max = keyin - 1
            elif (keyin < target):
                print("再大一點")
                min = keyin + 1
            print(f"您已經猜了{count}")
                
        else:
            print("請輸入提示範圍內的數字")
    
    is_play_again = input("您還要繼續嗎?y,n")
    if is_play_again == 'n':
        break
    

print("遊戲結束")