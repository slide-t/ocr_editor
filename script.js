const imageInput = document.getElementById("imageInput");
const previewImage = document.getElementById("previewImage");
const startBtn = document.getElementById("startBtn");
const progress = document.getElementById("progress");
const outputText = document.getElementById("outputText");
const copyBtn = document.getElementById("copyBtn");
const downloadBtn = document.getElementById("downloadBtn");

let selectedFile = null;

imageInput.addEventListener("change", e => {
  selectedFile = e.target.files[0];
  if (selectedFile) {
    const reader = new FileReader();
    reader.onload = function (event) {
      previewImage.src = event.target.result;
    };
    reader.readAsDataURL(selectedFile);
  }
});

startBtn.addEventListener("click", async () => {
  if (!selectedFile) {
    alert("Please select an image first!");
    return;
  }
  progress.textContent = "Processing...";

  const worker = await Tesseract.createWorker("eng", 1, {
    logger: m => {
      if (m.status === "recognizing text") {
        progress.textContent = `Progress: ${Math.round(m.progress * 100)}%`;
      }
    }
  });

  const { data } = await worker.recognize(selectedFile);
  outputText.value = data.text;
  await worker.terminate();
  progress.textContent = "Done ✅";
});

copyBtn.addEventListener("click", () => {
  outputText.select();
  document.execCommand("copy");
  alert("Copied to clipboard!");
});

downloadBtn.addEventListener("click", () => {
  const blob = new Blob([outputText.value], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "ocr_result.txt";
  a.click();
});
