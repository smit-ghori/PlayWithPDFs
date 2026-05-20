document.addEventListener("DOMContentLoaded", function () {

    const menuToggle =
        document.getElementById("menuToggle");

    const navLinks =
        document.querySelector(".nav-links");

    // =========================================
    // TOGGLE MENU
    // =========================================

    menuToggle.addEventListener("click", function (e) {

        e.stopPropagation();

        navLinks.classList.toggle("active");

        document.body.classList.toggle("menu-open");
    });

    // =========================================
    // PREVENT CLOSE WHEN CLICK INSIDE MENU
    // =========================================

    navLinks.addEventListener("click", function (e) {

        e.stopPropagation();
    });

    // =========================================
    // CLOSE WHEN CLICK OUTSIDE
    // =========================================

    document.addEventListener("click", function () {

        navLinks.classList.remove("active");

        document.body.classList.remove("menu-open");

        // close all dropdowns

        document
            .querySelectorAll(".dropdown")
            .forEach(drop => {

                drop.classList.remove("active");
            });
    });

    // =========================================
    // MOBILE DROPDOWNS
    // =========================================

    const dropdownLinks =
        document.querySelectorAll(".dropdown > a");

    dropdownLinks.forEach(link => {

        link.addEventListener("click", function (e) {

            if (window.innerWidth <= 768) {

                e.preventDefault();

                e.stopPropagation();

                const parent =
                    this.parentElement;

                // =====================================
                // CLOSE CURRENT IF OPEN
                // =====================================

                if (parent.classList.contains("active")) {

                    parent.classList.remove("active");

                    return;
                }

                // =====================================
                // CLOSE OTHER DROPDOWNS
                // =====================================

                document
                    .querySelectorAll(".dropdown")
                    .forEach(drop => {

                        drop.classList.remove("active");
                    });

                // =====================================
                // OPEN CURRENT
                // =====================================

                parent.classList.add("active");
            }
        });
    });

});