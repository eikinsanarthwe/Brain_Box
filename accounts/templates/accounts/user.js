document.addEventListener("DOMContentLoaded", function () {
  // Navigation switching
  const navItems = document.querySelectorAll(".nav-link");
  const sections = document.querySelectorAll(".main-content");

  // Initially show Home section
  document.getElementById("Home").style.display = "block";

  navItems.forEach((item) => {
    item.addEventListener("click", function () {
      // Remove active class
      navItems.forEach((link) => link.classList.remove("active"));
      this.classList.add("active");

      // Hide all sections
      sections.forEach((sec) => (sec.style.display = "none"));

      // Show selected section
      const sectionId = this.getAttribute("data-section");
      const target = document.getElementById(sectionId);
      if (target) {
        target.style.display = "block";
      }
    });
  });

  // Profile dropdown functionality
  const profileDropdown = document.getElementById("profileDropdown");
  const dropdownMenu = document.getElementById("dropdownMenu");

  if (profileDropdown && dropdownMenu) {
    profileDropdown.addEventListener("click", (e) => {
      e.stopPropagation();
      dropdownMenu.style.display =
        dropdownMenu.style.display === "block" ? "none" : "block";
    });

    document.addEventListener("click", function (event) {
      if (!profileDropdown.contains(event.target)) {
        dropdownMenu.style.display = "none";
      }
    });
  }

  // Level selection functionality
  const levelOptions = document.querySelectorAll(".level-option");

  levelOptions.forEach((option) => {
    option.addEventListener("click", function () {
      // Remove selected class from all options
      levelOptions.forEach((opt) => opt.classList.remove("selected"));

      // Add selected class to clicked option
      this.classList.add("selected");

      // Get the selected level
      const selectedLevel = this.getAttribute("data-level");

      // Filter and display courses based on level
      filterCoursesByLevel(selectedLevel);
    });
  });
});

// Course functions
window.startCourse = function (courseName) {
  alert("Now starting: " + courseName);
};

// Course data
const coursesData = [
  {
    title: "Intro to HTML",
    description: "Learn the basics of HTML to build web pages.",
    image: "HTML.jpg",
    levels: ["beginner"],
    rating: 4,
  },
  {
    title: "CSS Essentials",
    description: "Master styling and responsive design.",
    image: "Css.jpg",
    levels: ["beginner", "intermediate"],
    rating: 4,
  },
  {
    title: "JavaScript Basics",
    description: "Make your websites interactive.",
    image: "Java.jpg",
    levels: ["beginner", "intermediate"],
    rating: 4,
  },
  {
    title: "Python Basic",
    description: "Build your foundation in Python.",
    image: "Python.jpg",
    levels: ["beginner"],
    rating: 4,
  },
  {
    title: "Advanced JavaScript",
    description: "Deep dive into JS frameworks.",
    image: "Java.jpg",
    levels: ["intermediate", "advanced"],
    rating: 5,
  },
];

// Filter courses by level
function filterCoursesByLevel(level) {
  const filteredCourses = coursesData.filter((course) =>
    course.levels.includes(level)
  );

  const coursesContainer = document.getElementById("filtered-courses");
  coursesContainer.innerHTML = "";

  if (filteredCourses.length === 0) {
    coursesContainer.innerHTML = "<p>No courses found for this level.</p>";
    return;
  }

  // Create a card container div
  const cardContainer = document.createElement("div");
  cardContainer.className = "card-container";

  filteredCourses.forEach((course) => {
    const courseCard = document.createElement("div");
    courseCard.className = "course-card";
    courseCard.innerHTML = `
      <div class="card-photo">
        <img src="${course.image}" alt="${course.title}" class="course-image">
      </div>
      <div class="card-content">
        <h3>${course.title}</h3>
        <p>${course.description}</p>
        <button onclick="startCourse('${course.title}')">Start</button>
        <div class="rating">
          ${renderRatingStars(course.rating)}
        </div>
      </div>
    `;
    cardContainer.appendChild(courseCard);
  });

  coursesContainer.appendChild(cardContainer);
}

// Render rating stars
function renderRatingStars(rating) {
  let starsHTML = "";
  for (let i = 1; i <= 5; i++) {
    if (i <= rating) {
      starsHTML += '<i class="fas fa-star"></i>';
    } else if (i - 0.5 <= rating) {
      starsHTML += '<i class="fas fa-star-half-alt"></i>';
    } else {
      starsHTML += '<i class="far fa-star"></i>';
    }
  }
  return starsHTML;
}
function showSection(sectionId) {
  // Hide all sections
  document.querySelectorAll(".page-section").forEach((section) => {
    section.style.display = "none";
  });

  // Show selected section
  document.getElementById(sectionId).style.display = "block";
}

// Navigation click handler
document.querySelectorAll(".nav-link").forEach((link) => {
  link.addEventListener("click", function () {
    showSection(this.getAttribute("data-section"));
  });
});
