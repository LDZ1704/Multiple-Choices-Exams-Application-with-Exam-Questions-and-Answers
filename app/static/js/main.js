const correctAnswers = {
    q1: 'c',
    q2: 'b'
  };

  document.getElementById('quizForm').addEventListener('submit', function (e) {
    e.preventDefault();
    let score = 0;
    let total = Object.keys(correctAnswers).length;

    for (let q in correctAnswers) {
      const selected = document.querySelector(`input[name="${q}"]:checked`);
      if (selected && selected.value === correctAnswers[q]) {
        score++;
      }
    }

    const resultDiv = document.getElementById('result');
    resultDiv.textContent = `Bạn được ${score}/${total} điểm.`;
    resultDiv.classList.remove('d-none');
  });

  // Timer countdown 60s
  let timeLeft = 60;
  const timer = document.getElementById("timer");

  const countdown = setInterval(() => {
    let minutes = String(Math.floor(timeLeft / 60)).padStart(2, '0');
    let seconds = String(timeLeft % 60).padStart(2, '0');
    timer.textContent = `Thời gian: ${minutes}:${seconds}`;
    timeLeft--;

    if (timeLeft < 0) {
      clearInterval(countdown);
      document.getElementById("quizForm").dispatchEvent(new Event("submit"));
      timer.textContent = "Hết giờ!";
    }
  }, 1000);