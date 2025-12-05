module.exports = {
    content: [
        "./pages/**/*.{js,ts,jsx,tsx}",
        "./components/**/*.{js,ts,jsx,tsx}"
    ],
    theme: {
        extend: {
            colors: {
                primary: "hsl(210, 100%, 55%)",
                secondary: "hsl(210, 20%, 20%)",
                accent: "hsl(45, 100%, 55%)"
            }
        }
    },
    plugins: []
};
