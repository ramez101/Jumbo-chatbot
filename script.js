const chatMessages = document.getElementById("chat-messages");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const audio = document.getElementById("notif-sound");
const closeBtn = document.getElementById("close-chat");
const productsContainer = document.getElementById("products-container");
const productSpinner = document.getElementById("product-loading-spinner");

// Affiche un message bot classique
function afficherMessageBot(messageText) {
  const botMessage = document.createElement("div");
  botMessage.classList.add("bot");
  botMessage.innerHTML = messageText;
  chatMessages.appendChild(botMessage);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Affiche les cartes produit
function afficherCartesProduit(htmlContent) {
  productsContainer.innerHTML = htmlContent;
  setTimeout(() => {
    scrollCarousel(0);
  }, 100);
}

// Envoi d'un message (utilisateur ou forcé)
function sendMessage(messageForce = null) {
  const message = messageForce || userInput.value.trim();
  if (!message) return;

  const userMessage = document.createElement("div");
  userMessage.classList.add("user-message");
  userMessage.textContent = "Vous : " + message;
  chatMessages.appendChild(userMessage);
  userInput.value = "";
  chatMessages.scrollTop = chatMessages.scrollHeight;

  productSpinner.classList.remove("hidden");
  document.getElementById("products-wrapper").classList.add("blur-products");

  fetch("http://localhost:5000/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message })
  })
    .then(res => res.json())
    .then(data => {
      productSpinner.classList.add("hidden");
      document.getElementById("products-wrapper").classList.remove("blur-products");

      const reply = data.reply;

      if (reply.includes("carousel-item")) {
        const splitIndex = reply.indexOf('<div class="carousel-container">');
        const textPart = reply.slice(0, splitIndex);
        const sliderPart = reply.slice(splitIndex);

        if (textPart.trim()) afficherMessageBot(textPart);
        afficherCartesProduit(sliderPart);
      } else {
        afficherMessageBot(reply);
      }

      audio.play();

      fetch("http://localhost:5000/api/brands", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
      })
        .then(res => res.json())
        .then(data => {
          if (data.brands && data.brands.length > 0) {
            afficherBullesMarques(data.brands, message);
          }
        });
    })
    .catch(err => {
      productSpinner.classList.add("hidden");
      afficherMessageBot("❌ Une erreur est survenue.");
    });
}

// Évènements d'envoi
sendBtn.addEventListener("click", () => sendMessage());
userInput.addEventListener("keypress", function (e) {
  if (e.key === "Enter") sendMessage();
});

// Fermer chat
closeBtn.addEventListener("click", () => {
  document.body.classList.add("fade-out");
  setTimeout(() => {
    document.body.innerHTML = "";
    window.location.href = "https://www.jumbo.tn/";
  }, 500);
});

// Scroll du carousel
function scrollCarousel(direction) {
  const carousel = document.getElementById("carousel");
  if (!carousel) return;
  const itemWidth = carousel.querySelector(".carousel-item")?.offsetWidth || 250;
  carousel.scrollBy({ left: direction * (itemWidth + 32) * 2, behavior: 'smooth' });
}

// Affiche les bulles marques
function afficherBullesMarques(marques, categorie) {
  const container = document.createElement("div");
  container.className = "brand-bubbles";

  const texteIntro = document.createElement("div");
  texteIntro.className = "bot";
  texteIntro.textContent = "📦 Choisissez une marque disponible :";
  chatMessages.appendChild(texteIntro);

  marques.forEach(marque => {
    const b = document.createElement("button");
    b.className = "brand-bubble";
    b.innerText = marque;
    b.onclick = () => {
      const message = categorie + " " + marque;
      sendMessage(message);
    };
    container.appendChild(b);
  });

  chatMessages.appendChild(container);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Affiche toutes les bulles regroupées dans un seul conteneur
function afficherBullesInitiales() {
  // Si déjà créé, ne rien faire
  if (document.querySelector('.brand-bubbles.initial')) return;

  const container = document.createElement('div');
  container.className = 'brand-bubbles initial';

  // Bulle Service client
  const bubbleServiceClient = document.createElement('div');
  bubbleServiceClient.className = 'brand-bubble';
  bubbleServiceClient.textContent = '👨🏻‍💻 Service client';
  bubbleServiceClient.onclick = afficherInfosServiceClient;
  container.appendChild(bubbleServiceClient);

  // Bulle Showroom
  const bubbleShowroom = document.createElement('div');
  bubbleShowroom.className = 'brand-bubble';
  bubbleShowroom.textContent = '🏢 Showroom';
  bubbleShowroom.onclick = afficherInfosShowroom;
  container.appendChild(bubbleShowroom);

  // Bulle Demande Crédit BTK
  const bubbleCreditBTK = document.createElement('div');
  bubbleCreditBTK.className = 'brand-bubble';
  bubbleCreditBTK.textContent = '💳 Demande Crédit BTK';
  bubbleCreditBTK.onclick = () => {
    window.open('https://chakira-distribution.com/jumbo2/content/10-demande-de-credit', '_blank');
  };
  container.appendChild(bubbleCreditBTK);

  


  chatMessages.appendChild(container);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Affiche infos Service client (avec contrôle d'existence)
function afficherInfosServiceClient() {
  if (document.getElementById('service-client-message')) return;

  const messageContainer = document.createElement('div');
  messageContainer.className = 'bot';
  messageContainer.id = 'service-client-message';
  messageContainer.style.position = 'relative';

  messageContainer.innerHTML = `
    <span onclick="fermerServiceClient()" style="
      position: absolute;
      top: 5px;
      right: 10px;
      cursor: pointer;
      font-size: 18px;
      color: #e74c3c;
    ">✖</span>

    📱 <strong>Contactez-nous :</strong><br>
    📞 <strong>92 032 000</strong> ou <strong>92 927 000</strong><br><br>
    ✉️ <strong>Par mail :</strong><br>
    ✍️ contact@jumbo.tn <br>
  `;

  chatMessages.appendChild(messageContainer);
  scrollChatToBottom();
}

function fermerServiceClient() {
  const element = document.getElementById('service-client-message');
  if (element) element.remove();
}

// Affiche infos Showroom (avec contrôle d'existence)
function afficherInfosShowroom() {
  if (document.getElementById('showroom-message')) return;

  const messageContainer = document.createElement('div');
  messageContainer.className = 'bot';
  messageContainer.id = 'showroom-message';
  messageContainer.style.position = 'relative';

  messageContainer.innerHTML = `
    <span onclick="fermerShowroom()" style="
      position: absolute;
      top: 5px;
      right: 10px;
      cursor: pointer;
      font-size: 18px;
      color: #e74c3c;
    ">✖</span>

    🏢 <strong>Showroom :</strong><br>
    Rue de Socrate, Zone Industrielle Kheireddine, La Goulette<br><br>
    <a href="https://maps.app.goo.gl/TbR2wcAjMTMFn3sn9" target="_blank" class="product-link">
      📍 Voir l'emplacement sur Google Maps
    </a>
  `;

  chatMessages.appendChild(messageContainer);
  scrollChatToBottom();
}

function fermerShowroom() {
  const element = document.getElementById('showroom-message');
  if (element) element.remove();
}

// Scroll automatique vers le bas du chat
function scrollChatToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Au chargement du DOM, on affiche le message de bienvenue et les bulles
window.addEventListener("DOMContentLoaded", () => {
  const welcomeMessage = document.createElement("div");
  welcomeMessage.className = "bot";
  welcomeMessage.innerText = "👋 Bonjour ! Je suis votre assistant IA. Comment puis-je vous aider aujourd’hui ?";
  chatMessages.appendChild(welcomeMessage);

  afficherBullesInitiales();
  scrollChatToBottom();
});
