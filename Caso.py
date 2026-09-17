from dataclasses import dataclass
import tkinter as tk


class Lista:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    def find(self, code):
        for x in self.items:
            if x.code == code:
                return x
        return None

    def all(self):
        return self.items


class Cola:
    def __init__(self):
        self.items = []
        self.front = 0

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        if self.front >= len(self.items):
            raise ValueError("Queue empty")
        x = self.items[self.front]
        self.front += 1
        if self.front > len(self.items) // 2:
            self.items = self.items[self.front:]
            self.front = 0
        return x

    def size(self):
        return len(self.items) - self.front

    def view(self):
        return self.items[self.front:]


class Pila:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.items:
            raise ValueError("Stack empty")
        return self.items.pop()

    def view(self):
        return self.items[:]

    def clear(self):
        self.items.clear()


@dataclass
class Product:
    code: str
    recipe: list


@dataclass
class Pedido:
    number: int
    canal: str
    codigo: str
    omit: list
    minuto: int
    estado: str = "EN_COLA"


class Kitchen:
    def __init__(self):
        self.catalog = Lista()
        self.mostrador = Cola()
        self.domicilio = Cola()
        self.stack = Pila()
        self.current = None
        self.product = None
        self.n = 1
        self.counter = 0
        self.logs = []
        self.metrics = {"total": 0, "ready": 0, "cancel": 0, "waste": 0, "errors": 0}

    def load_catalog(self, data):
        for d in data:
            p = Product(d["code"], d["recipe"])
            if self.catalog.find(p.code):
                raise ValueError("duplicate code")
            self.catalog.add(p)

    def register(self, canal, code, omit, minuto):
        p = self.catalog.find(code)
        if not p:
            raise ValueError("product not found")
        q = self.mostrador if canal == "MOSTRADOR" else self.domicilio
        if q.size() >= 5:
            raise ValueError("R7: queue full")
        pedido = Pedido(self.n, canal, code, omit, minuto)
        self.n += 1
        q.enqueue(pedido)
        self.metrics["total"] += 1

    def next_order(self):
        if self.current:
            raise ValueError("already assembling")
        if self.mostrador.size() == 0 and self.domicilio.size() == 0:
            raise ValueError("no orders")

        if self.domicilio.size() == 0:
            self.current = self.mostrador.dequeue()
            self.counter += 1
        elif self.mostrador.size() == 0:
            self.current = self.domicilio.dequeue()
            self.counter = 0
        elif self.counter >= 3:
            self.current = self.domicilio.dequeue()
            self.counter = 0
        else:
            self.current = self.mostrador.dequeue()
            self.counter += 1

        self.product = self.catalog.find(self.current.codigo)
        self.stack.clear()
        return self.current

    def expected(self):
        if not self.product:
            return []
        return [x for x in self.product.recipe if x not in self.current.omit]

    def place(self, layer):
        if not self.current:
            raise ValueError("no active order")
        exp = self.expected()
        if self.stack.view() == exp[:len(self.stack.view())] and layer == exp[len(self.stack.view())]:
            self.stack.push(layer)
            return
        self.stack.push(layer)
        self.metrics["errors"] += 1

    def remove(self):
        if not self.stack.view():
            raise ValueError("empty stack")
        x = self.stack.pop()
        self.metrics["waste"] += 1
        return x

    def verify(self):
        exp = self.expected()
        cur = self.stack.view()
        ok = cur == exp
        return {"ok": ok, "expected": exp, "stack": cur}

    def ready(self, minute):
        if self.verify()["ok"] is False:
            raise ValueError("recipe not complete")
        self.metrics["ready"] += 1
        self.stack.clear()
        self.current = None
        self.product = None
        return "LISTO"

    def cancel(self):
        while self.stack.view():
            self.remove()
        self.current = None
        self.product = None
        self.metrics["cancel"] += 1
        return "CANCELADO"


DATA = [
    {"code": "BRG-01", "recipe": ["pan_base", "salsa", "carne", "queso", "cebolla", "tomate", "pan_tapa"]},
    {"code": "BRG-02", "recipe": ["pan_base", "salsa", "carne", "queso", "tomate", "pan_tapa"]},
    {"code": "FRI-01", "recipe": ["papas", "salsa", "queso", "pan_tapa"]},
]


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Kitchen")
        self.root.geometry("1200x700")
        self.system = Kitchen()
        self.system.load_catalog(DATA)

        self.build_ui()
        self.refresh()

    def build_ui(self):
        self.row = tk.Frame(self.root)
        self.row.pack(fill="x", padx=10, pady=10)

        tk.Button(self.row, text="Order", command=self.show_order).pack(side="left")
        tk.Button(self.row, text="Kitchen", command=self.show_kitchen).pack(side="left")
        tk.Button(self.row, text="Station", command=self.show_station).pack(side="left")
        tk.Button(self.row, text="Report", command=self.show_report).pack(side="left")

        self.pages = {}
        self.pages["order"] = tk.Frame(self.root)
        self.pages["kitchen"] = tk.Frame(self.root)
        self.pages["station"] = tk.Frame(self.root)
        self.pages["report"] = tk.Frame(self.root)

        self.make_order()
        self.make_kitchen()
        self.make_station()
        self.make_report()

        self.show_order()

    def show_order(self):
        for p in self.pages.values():
            p.pack_forget()
        self.pages["order"].pack(fill="both", expand=True)

    def show_kitchen(self):
        for p in self.pages.values():
            p.pack_forget()
        self.pages["kitchen"].pack(fill="both", expand=True)

    def show_station(self):
        for p in self.pages.values():
            p.pack_forget()
        self.pages["station"].pack(fill="both", expand=True)

    def show_report(self):
        for p in self.pages.values():
            p.pack_forget()
        self.pages["report"].pack(fill="both", expand=True)

    def make_order(self):
        f = self.pages["order"]
        tk.Label(f, text="Channel").pack()
        self.canal = tk.StringVar(value="MOSTRADOR")
        tk.OptionMenu(f, self.canal, "MOSTRADOR", "DOMICILIO").pack()

        tk.Label(f, text="Product").pack()
        self.product_var = tk.StringVar()
        self.product_combo = tk.OptionMenu(f, self.product_var, *[p.code for p in self.system.catalog.all()])
        self.product_combo.pack()

        tk.Label(f, text="Omit layers").pack()
        self.omit_var = tk.StringVar(value="")
        tk.Entry(f, textvariable=self.omit_var).pack()

        tk.Label(f, text="Minute").pack()
        self.minute = tk.StringVar(value="10")
        tk.Entry(f, textvariable=self.minute).pack()

        tk.Button(f, text="Register order", command=self.reg_order).pack(pady=10)
        tk.Button(f, text="Load sample", command=self.load_sample).pack()

    def make_kitchen(self):
        f = self.pages["kitchen"]
        self.most = tk.Listbox(f, width=30, height=10)
        self.most.pack(side="left", padx=10)
        self.dom = tk.Listbox(f, width=30, height=10)
        self.dom.pack(side="left", padx=10)
        tk.Button(f, text="Next order", command=self.next_order).pack(side="left", padx=10)
        self.counter_label = tk.Label(f, text="Counter: 0")
        self.counter_label.pack(side="left")

    def make_station(self):
        f = self.pages["station"]
        self.stack_box = tk.Listbox(f, width=25, height=12)
        self.stack_box.pack(side="left", padx=10)

        tk.Label(f, text="Recipe").pack(side="left")
        self.recipe_box = tk.Listbox(f, width=25, height=12)
        self.recipe_box.pack(side="left", padx=10)

        self.layer_entry = tk.Entry(f)
        self.layer_entry.pack(side="left")

        tk.Button(f, text="Put layer", command=self.put_layer).pack(side="left")
        tk.Button(f, text="Remove layer", command=self.remove_layer).pack(side="left")
        tk.Button(f, text="Verify", command=self.verify).pack(side="left")
        tk.Button(f, text="Ready", command=self.ready).pack(side="left")
        tk.Button(f, text="Cancel", command=self.cancel).pack(side="left")

        self.message = tk.Label(f, text="")
        self.message.pack(side="bottom", pady=10)

    def make_report(self):
        f = self.pages["report"]
        self.report_box = tk.Text(f, width=60, height=20)
        self.report_box.pack()

    def reg_order(self):
        try:
            code = self.product_var.get()
            omit = [x.strip() for x in self.omit_var.get().split(',') if x.strip()]
            self.system.register(self.canal.get(), code, omit, int(self.minute.get()))
            self.message['text'] = "Order registered"
        except Exception as e:
            self.message['text'] = str(e)
        self.refresh()

    def next_order(self):
        try:
            self.system.next_order()
            self.message['text'] = "Order selected"
        except Exception as e:
            self.message['text'] = str(e)
        self.refresh()

    def put_layer(self):
        try:
            self.system.place(self.layer_entry.get())
            self.message['text'] = "Layer placed"
        except Exception as e:
            self.message['text'] = str(e)
        self.refresh()

    def remove_layer(self):
        try:
            self.system.remove()
            self.message['text'] = "Layer removed"
        except Exception as e:
            self.message['text'] = str(e)
        self.refresh()

    def verify(self):
        try:
            r = self.system.verify()
            self.message['text'] = "OK" if r["ok"] else "Wrong recipe"
        except Exception as e:
            self.message['text'] = str(e)
        self.refresh()

    def ready(self):
        try:
            self.system.ready(int(self.minute.get()))
            self.message['text'] = "Ready"
        except Exception as e:
            self.message['text'] = str(e)
        self.refresh()

    def cancel(self):
        try:
            self.system.cancel()
            self.message['text'] = "Canceled"
        except Exception as e:
            self.message['text'] = str(e)
        self.refresh()

    def load_sample(self):
        self.system = Kitchen()
        self.system.load_catalog(DATA)
        self.product_var.set("BRG-01")
        self.refresh()

    def refresh(self):
        self.most.delete(0, tk.END)
        self.dom.delete(0, tk.END)
        for x in self.system.mostrador.view():
            self.most.insert(tk.END, f"#{x.number} {x.codigo}")
        for x in self.system.domicilio.view():
            self.dom.insert(tk.END, f"#{x.number} {x.codigo}")
        self.counter_label.config(text=f"Counter: {self.system.counter}")

        self.stack_box.delete(0, tk.END)
        for layer in self.system.stack.view():
            self.stack_box.insert(tk.END, layer)

        self.recipe_box.delete(0, tk.END)
        if self.system.current and self.system.product:
            for layer in self.system.expected():
                self.recipe_box.insert(tk.END, layer)

        self.report_box.delete(1.0, tk.END)
        self.report_box.insert(tk.END, f"Total: {self.system.metrics['total']}\n")
        self.report_box.insert(tk.END, f"Ready: {self.system.metrics['ready']}\n")
        self.report_box.insert(tk.END, f"Cancel: {self.system.metrics['cancel']}\n")
        self.report_box.insert(tk.END, f"Waste: {self.system.metrics['waste']}\n")
        self.report_box.insert(tk.END, f"Errors: {self.system.metrics['errors']}\n")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
