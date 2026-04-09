Modulo Odoo 17 per il calcolo automatico del **New Business** per venditore.

---

## Changelog v1.17
- **Fix campo Anno**: il campo `Anno` ora mostra `2026` invece di `2.026`
  (il tipo è cambiato da `Integer` a `Char`, eliminando il separatore migliaia)
- **Fix Data rif. Canone/Corpo**: il campo `Data rif.` per i prodotti
  Canone / Offerta a corpo ora riporta correttamente la data della
  **prima milestone**, non la data di conferma ordine

---

## Struttura file

```
new_business_v1_17/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── new_business_v1_17.py   ← LOGICA PRINCIPALE (vista SQL)
├── security/
│   └── ir.model.access.csv
├── views/
│   └── new_business_v1_17_views.xml
└── README.md
```

---

## Logica di calcolo

### Canone / Offerta a corpo
- **Discriminante**: `service_policy = delivered_milestones` AND `auto_milestone = True`
- **Valore**: solo la **prima milestone** (ordinata per data_deadline ASC)
- **Anno/Mese NB**: quelli della **prima milestone** (NON della data ordine)
- **Data rif.**: data (deadline) della **prima milestone**
  va nel 2026, non nel 2025. Se un ordine ha 3 canoni + 1 attivazione nel 2025:
  - NB 2025 = attivazione intera + 1 canone (primo anno)
  - NB 2026 = niente da questo ordine

### Attivazione
- **Discriminante**: `service_policy = delivered_milestones` AND `auto_milestone = False`
- **Valore**: intero (`price_subtotal`)
- **Anno/Mese NB**: data conferma ordine

### Pacchetti Ore
- **Discriminante**: `service_policy IN (ordered_prepaid, delivered_manual)`
  AND categoria IN ('Pacchetti Ore BU Digital Innovation', 'Pacchetti Ore BU Catering')
- **Valore**: intero (`price_subtotal`)
- **Anno/Mese NB**: data conferma ordine
- **Business Unit**: derivata dal nome categoria prodotto

---

## Cosa è escluso
- Preventivi (stato `draft`, `sent`)
- Ordini annullati (stato `cancel`)

---

## Installazione su Odoo.sh

1. Copiare la cartella `new_business_v1_17` nella directory
   `custom-addons` (o equivalente) del repository Git collegato a Odoo.sh
2. Fare `git add`, `git commit`, `git push`
3. Odoo.sh rileva automaticamente il nuovo modulo e ricostruisce l'istanza
4. Andare su **App** in Odoo → cercare "New Business Report" → **Installa**

---

## Uso nel foglio di calcolo Odoo

Una volta installato, il modello `new.business.v1.17` è disponibile
come sorgente dati. Esempio di formula pivot per anno/venditore:

```
=ODOO.PIVOT(1, "amount_new_business", "salesperson_id", "new_business_year", 2025)
```

---

## Note di manutenzione

Se vengono aggiunte nuove categorie Pacchetti Ore, aggiornare il blocco 3
della query SQL in `models/new_business_v1_17.py` (clausola `IN` e `CASE`).
