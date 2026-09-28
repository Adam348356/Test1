<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Taschenrechner</title>

  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
    }

    body {
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      background: #1a1a1a;
    }

    .calculator {
      width: 340px;
      padding: 20px;
      border-radius: 25px;
      background: #222;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
    }

    .display {
      width: 100%;
      height: 100px;
      margin-bottom: 20px;
      padding: 20px;
      border-radius: 15px;
      background: #111;
      color: white;
      display: flex;
      align-items: flex-end;
      justify-content: flex-end;
      font-size: 40px;
      overflow: hidden;
    }

    .buttons {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
    }

    button {
      height: 65px;
      border: none;
      border-radius: 15px;
      font-size: 22px;
      cursor: pointer;
      background: #333;
      color: white;
      transition: 0.15s;
    }

    button:hover {
      background: #444;
      transform: scale(1.03);
    }

    button:active {
      transform: scale(0.96);
    }

    .operator {
      background: #ff9500;
    }

    .operator:hover {
      background: #ffad33;
    }

    .clear {
      background: #a5a5a5;
      color: black;
    }

    .equals {
      background: #34c759;
    }

    .equals:hover {
      background: #4cd964;
    }```html

    .zero {
      grid-column: span 2;
    }
  </style>
</head>

<body>

  <div class="calculator">

    <div id="display" class="display">0</div>

    <div class="buttons">
      <button class="clear" onclick="clearDisplay()">AC</button>
      <button onclick="deleteLast()">⌫</button>
      <button onclick="addToDisplay('%')">%</button>
      <button class="operator" onclick="addToDisplay('/')">÷</button>

      <button onclick="addToDisplay('7')">7</button>
      <button onclick="addToDisplay('8')">8</button>
      <button onclick="addToDisplay('9')">9</button>
      <button class="operator" onclick="addToDisplay('*')">×</button>

      <button onclick="addToDisplay('4')">4</button>
      <button onclick="addToDisplay('5')">5</button>
      <button onclick="addToDisplay('6')">6</button>
      <button class="operator" onclick="addToDisplay('-')">−</button>

      <button onclick="addToDisplay('1')">1</button>
      <button onclick="addToDisplay('2')">2</button>
      <button onclick="addToDisplay('3')">3</button>
      <button class="operator" onclick="addToDisplay('+')">+</button>
```html
      <button class="zero" onclick="addToDisplay('0')">0</button>
      <button onclick="addToDisplay('.')">.</button>
      <button class="equals" onclick="calculate()">=</button>
    </div>

  </div>

  <script>
    const display = document.getElementById("display");

    function addToDisplay(value) {
      if (display.textContent === "0" || display.textContent === "Fehler") {
        display.textContent = value;
      } else {
        display.textContent += value;
      }
    }

    function clearDisplay() {
      display.textContent = "0";
    }

    function deleteLast() {
      if (
        display.textContent === "Fehler" ||
        display.textContent.length <= 1
      ) {
        display.textContent = "0";
      } else {
        display.textContent =
          display.textContent.slice(0, -1);
      }
    }

    function calculate() {
      try {
        let expression = display.textContent;

        // Prozentzeichen in Dezimalzahl umwandeln
        expression = expression.replace(
          /(\d+(?:\.\d+)?)%/g,
          "($1/100)"
        );

        // Nur mathematisch relevante Zeichen erlauben
        if (!/^[0-9+\-*/().\s]+$/.test(expression)) {
          throw new Error();
        }

        const result = Function(
          '"use strict"; return (' + expression + ')'
        )();

        if (!Number.isFinite(result)) {
          throw new Error();
        }

        display.textContent =
          Number.isInteger(result)
            ? result
            : parseFloat(result.toFixed(10));

      } catch {
        display.textContent = "Fehler";
      }
    }

    // Tastatur-Unterstützung
    document.addEventListener("keydown", (event) => {

      const key = event.key;

      if (
        /[0-9+\-*/().%]/.test(key)
      ) {
        addToDisplay(key);
      }

      if (key === "Enter" || key === "=") {
        calculate();
      }

      if (key === "Backspace") {
        deleteLast();
      }

      if (key === "Escape") {
        clearDisplay();
      }
    });
  </script>

</body>
</html>

