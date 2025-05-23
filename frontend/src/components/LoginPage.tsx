

const LoginPage = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-primary font-poppins">
      <div className="bg-secondary p-8 rounded-lg shadow-lg w-full max-w-md">
        <h2 className="text-3xl font-semibold text-primaryText mb-6 text-center">Welcome Back</h2>
        <form className="space-y-5">
          <div>
            <label htmlFor="email" className="block text-sm text-secondaryText mb-1">Email</label>
            <input
              type="email"
              id="email"
              className="w-full px-4 py-2 bg-primary border border-primaryAccent rounded focus:outline-none focus:ring-2 focus:ring-primaryAccent text-primaryText placeholder-secotext-secondaryText"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm text-secondaryText mb-1">Password</label>
            <input
              type="password"
              id="password"
              className="w-full px-4 py-2 bg-primary border border-primaryAccent rounded focus:outline-none focus:ring-2 focus:ring-primaryAccent text-primaryText placeholder-secotext-secondaryText"
              placeholder="••••••••"
            />
          </div>
          <div className="flex items-center justify-between text-sm text-secondaryText">
            <label className="flex items-center">
              <input type="checkbox" className="form-checkbox text-primaryAccent mr-2" />
              Remember me
            </label>
            <a href="#" className="hover:underline text-primaryAccent">Forgot Password?</a>
          </div>
          <button
            type="submit"
            className="w-full bg-primaryAccent hover:bg-secondaryAccent text-primary font-semibold py-2 px-4 rounded transition duration-300"
          >
            Sign In 
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-secondaryText">
          Don't have an account? <a href="#" className="text-primaryAccent hover:underline">Sign up</a>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
