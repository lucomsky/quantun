Схема уведомлений о времени следующего доната

![](sell_food.svg)
<details>

```
@startuml sell_food
actor       Seller       as usr
participant      "Sell food bot"      as gfb
database    "Active sellers list"    as fdb

usr --> usr: Пользователь хочет создать заявку на размещение КОРМА
usr -> gfb: Создание новой заявки
usr <-- gfb: Введите адрес XMR
usr -> gfb: Адрес XMR продавца
usr <-- gfb: Введите доступный amount
usr -> gfb: Доступный размер активов
gfb --> gfb: TBD: Холд активов
note right
В случае нахождения способа
холда актива на момент пока заявка открыта -
нет необходимости в верификации продавца
так как верификацией является холд объема средств
end note
gfb <-> fdb: Создание открытой активной заявки
usr <- gfb: Панель управления открытой заявкой
note right
В один момент времени у продавца может быть открыта только 1 заявка.
end note
@enduml
```

</details>